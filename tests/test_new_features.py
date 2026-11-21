"""Tests for the new finale features: blast radius, freshness,
load-bearing (PageRank), evidence grades, who-to-ask, show-the-query,
and the /decisions + /health pages.

Fixtures are small hand-built graphs — the behaviour must hold on the
graph's own rules, not on one lucky demo question. Live parity tests
(Neo4j store == SQLite store) run only when NEO4J_* env vars are set.
Run: python3 -m pytest tests/ -q
"""
import os

import pytest

import app as ui_app
from whycode.features import (
    blast_radius,
    decision_freshness,
    decision_health,
    evidence_grade,
    governed_files,
    load_bearing,
    who_to_ask,
)
from whycode.graph import GraphStore
from whycode.neo4j_chain import Neo4jGraphStore, store_from_env

LIVE = bool(os.environ.get("NEO4J_URI")
            and os.environ.get("NEO4J_USERNAME")
            and os.environ.get("NEO4J_PASSWORD"))
needs_live = pytest.mark.skipif(not LIVE, reason="NEO4J_* env vars not set")


def fixture_store():
    """A small graph with dated decisions, governed files, and authors.

    doc d1 (2020-01-01) mentions f1; f1 is touched by c1 (2019, before
    the decision) and c2 (2021, after it) and c3 (2022, after it).
    c2 fixes issue i1; c1/c2/c3 are authored by p1/p1/p2. doc d2
    (2021-06-01) mentions f2, untouched since. doc d3 has no date.
    """
    s = GraphStore()
    s.add_entity("d1", "doc", "Decision one", ":Created: 2020-01-01\n\nBody.",
                 "u/d1")
    s.add_entity("d2", "doc", "Decision two", ":Created: 2021-06-01\n\nBody.",
                 "u/d2")
    s.add_entity("d3", "doc", "Undated decision", "No date in here.", "u/d3")
    s.add_entity("f1", "file", "a.py", "", "")
    s.add_entity("f2", "file", "b.py", "", "")
    s.add_entity("c1", "commit", "Old change to a", "before", "u/c1",
                 "2019-05-01T00:00:00Z")
    s.add_entity("c2", "commit", "New change to a", "after", "u/c2",
                 "2021-03-01T00:00:00Z")
    s.add_entity("c3", "commit", "Newer change to a", "after", "u/c3",
                 "2022-07-01T00:00:00Z")
    s.add_entity("i1", "issue", "Bug in a", "broke", "u/i1")
    s.add_entity("p1", "person", "alice", "", "")
    s.add_entity("p2", "person", "bob", "", "")
    s.add_edge("d1", "f1", "mentions")
    s.add_edge("d2", "f2", "mentions")
    s.add_edge("c1", "f1", "touches")
    s.add_edge("c2", "f1", "touches")
    s.add_edge("c3", "f1", "touches")
    s.add_edge("c2", "i1", "fixes")
    s.add_edge("c1", "p1", "authored")
    s.add_edge("c2", "p1", "authored")
    s.add_edge("c3", "p2", "authored")
    return s


@pytest.fixture()
def client():
    ui_app.app.config["TESTING"] = True
    with ui_app.app.test_client() as c:
        yield c


@pytest.fixture(scope="module")
def neo4j_store():
    store = store_from_env()
    yield store
    if store is not None:
        store.close()


# --- Evidence grades -------------------------------------------------------

def test_grades_by_kind():
    assert evidence_grade({"kind": "doc"}) == (
        "A", "formal decision record")
    assert evidence_grade({"kind": "pr"}) == ("B", "reviewed change")
    assert evidence_grade({"kind": "commit"}) == ("C", "implementation")
    assert evidence_grade({"kind": "issue"}) == ("D", "request / discussion")


def test_person_and_file_are_never_graded():
    assert evidence_grade({"kind": "person"}) is None
    assert evidence_grade({"kind": "file"}) is None


# --- Governed files + blast radius ------------------------------------------

def test_governed_files_from_mentions_and_touches():
    s = fixture_store()
    d1 = s.get_entity("d1")
    files = governed_files(s, d1, evidence=[])
    assert set(files) == {"f1"}


def test_blast_radius_counts_and_people():
    s = fixture_store()
    d1 = s.get_entity("d1")
    blast = blast_radius(s, d1, evidence=[])
    assert blast["file_count"] == 1
    # c1, c2, c3 all touch f1.
    assert blast["commit_count"] == 3
    # i1 is fixed by c2.
    assert blast["issue_count"] == 1
    assert blast["decision_count"] == 0
    # alice authored c1 + c2 (2), bob authored c3 (1).
    assert [p["title"] for p in blast["people"]] == ["alice", "bob"]
    assert who_to_ask(blast) == [
        {"id": "p1", "title": "alice", "count": 2},
        {"id": "p2", "title": "bob", "count": 1},
    ]


def test_blast_radius_commit_order_most_recent_first():
    s = fixture_store()
    d1 = s.get_entity("d1")
    blast = blast_radius(s, d1, evidence=[])
    assert [c["id"] for c in blast["commits"]] == ["c3", "c2", "c1"]


def test_blast_radius_caps_display_lists_not_counts():
    s = fixture_store()
    d1 = s.get_entity("d1")
    blast = blast_radius(s, d1, evidence=[], max_commits=2)
    assert len(blast["commits"]) == 2
    assert blast["commit_count"] == 3


# --- Freshness --------------------------------------------------------------

def test_freshness_counts_churn_after_decision_date():
    s = fixture_store()
    d1 = s.get_entity("d1")
    fresh = decision_freshness(s, d1, evidence=[])
    assert fresh is not None
    assert fresh["date"] == "2020-01-01"
    # c2 (2021) and c3 (2022) are after; c1 (2019) is before.
    assert fresh["churn"] == 2
    assert fresh["last_change"] == "2022-07-01"
    assert "changed 2 times since, last 2022-07-01" in fresh["line"]
    assert "stale" not in fresh["line"].lower()


def test_freshness_zero_churn_line():
    s = fixture_store()
    d2 = s.get_entity("d2")
    fresh = decision_freshness(s, d2, evidence=[])
    assert fresh is not None
    assert fresh["churn"] == 0
    assert fresh["line"] == ("Decided 2021-06-01. No changes to its code "
                             "since it was decided.")


def test_freshness_omitted_without_date():
    s = fixture_store()
    d3 = s.get_entity("d3")
    assert decision_freshness(s, d3, evidence=[]) is None


def test_freshness_omitted_without_governed_files():
    s = GraphStore()
    s.add_entity("d9", "doc", "Lonely decision",
                 ":Created: 2020-01-01\n\nBody.", "u/d9")
    assert decision_freshness(s, s.get_entity("d9"), evidence=[]) is None


# --- Load-bearing (PageRank) + health --------------------------------------

def test_load_bearing_ranks_central_doc_first():
    s = GraphStore()
    # d1 is pointed at by two docs (supersedes in-links); d2 by none.
    s.add_entity("d1", "doc", "Central decision", ":Created: 2020-01-01",
                 "u/d1")
    s.add_entity("d2", "doc", "Leaf decision", ":Created: 2020-01-01",
                 "u/d2")
    s.add_entity("d0", "doc", "Old decision", ":Created: 2019-01-01",
                 "u/d0")
    s.add_edge("d0", "d1", "supersedes")
    s.add_edge("d2", "d1", "supersedes")
    rows = load_bearing(s, top_n=10)
    assert rows[0]["id"] == "d1"
    assert rows[0]["score"] > rows[1]["score"]
    assert all("score" in r and "links" in r for r in rows)


def test_decision_health_ranks_by_churn_then_recency():
    s = fixture_store()
    rows = decision_health(s, top_n=10)
    # d1 has churn 2, d2 has churn 0; d3 is undated and excluded.
    assert [r["id"] for r in rows] == ["d1", "d2"]
    assert rows[0]["churn"] == 2
    assert rows[1]["churn"] == 0
    assert rows[1]["file_count"] == 1


# --- Show the query ---------------------------------------------------------

def test_sqlite_chain_query_names_the_entity():
    s = fixture_store()
    q = s.chain_query("d1")
    assert "WHERE g.src = 'd1'" in q
    assert "WHERE g.dst = 'd1'" in q
    assert "SELECT" in q


def test_neo4j_chain_query_is_cypher_without_credentials():
    snapshot = (
        {"d1": {"id": "d1", "kind": "doc", "title": "T", "body": "",
                "url": "", "created_at": ""}},
        {"d1": []},
        {"d1": []},
    )
    store = Neo4jGraphStore(snapshot=snapshot)
    q = store.chain_query("d1")
    assert "MATCH (n:Entity)" in q
    assert "MATCH (a:Entity)-[r]->(b:Entity)" in q
    assert "password" not in q.lower()
    assert store.all_entities()[0]["id"] == "d1"
    assert store.all_edges() == []


# --- Live parity: Neo4j == SQLite ------------------------------------------

@needs_live
def test_live_blast_freshness_pagerank_parity(neo4j_store):
    from whycode.qa import ask
    sq = GraphStore("data/whycode.db")
    for question in (
            "Why does ignore_warnings match substrings by default?",
            "Why does Django need a steering council?"):
        a = ask(sq, question)
        b = ask(neo4j_store, question)
        assert blast_radius(sq, a["match"], a["evidence"]) == \
            blast_radius(neo4j_store, b["match"], b["evidence"])
        assert decision_freshness(sq, a["match"], a["evidence"]) == \
            decision_freshness(neo4j_store, b["match"], b["evidence"])
    assert load_bearing(sq) == load_bearing(neo4j_store)
    assert decision_health(sq) == decision_health(neo4j_store)


# --- UI ---------------------------------------------------------------------

def test_decisions_page_lists_top_docs(client):
    r = client.get("/decisions")
    assert r.status_code == 200
    assert b"Load-bearing decisions" in r.data
    assert b"PageRank" in r.data


def test_health_page_lists_ranked_decisions(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert b"Decision health" in r.data
    assert b"churn" in r.data.lower()


def test_digest_page_lists_all_three_sections(client):
    r = client.get("/digest")
    assert r.status_code == 200
    assert b"Monthly digest" in r.data
    assert b"New decisions" in r.data
    assert b"What changed" in r.data
    assert b"Top experts" in r.data


def test_digest_sections_are_ordered():
    from whycode.features import digest
    data = digest(GraphStore("data/whycode.db"))
    assert len(data["new_decisions"]) == 10
    dates = [d["date"] for d in data["new_decisions"]]
    assert dates == sorted(dates, reverse=True)
    assert len(data["recent_changes"]) == 10
    cdates = [c["date"] for c in data["recent_changes"]]
    assert cdates == sorted(cdates, reverse=True)
    assert len(data["top_experts"]) == 10
    counts = [p["commits"] for p in data["top_experts"]]
    assert counts == sorted(counts, reverse=True)


def test_answer_page_shows_blast_grades_who_and_query(client):
    r = client.get("/", query_string={
        "q": "Why does ignore_warnings match substrings by default?"})
    assert r.status_code == 200
    assert b"Blast radius" in r.data
    assert b"Grade" in r.data
    assert b"talk to:" in r.data
    assert b"Show the query" in r.data
    # The query shown follows the serving store: SQL neighbour queries
    # from SQLite, Cypher snapshot queries from Neo4j.
    assert (b"SELECT e.*, g.relation FROM edges g" in r.data
            or b"MATCH (n:Entity)" in r.data)


def test_refusal_carries_no_new_features(client):
    r = client.get("/", query_string={
        "q": "Why does Django use microservices?"})
    assert r.status_code == 200
    assert b"refuses to answer" in r.data
    assert b"Blast radius" not in r.data
    assert b"Show the query" not in r.data
