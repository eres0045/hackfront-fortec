"""Neo4j serving tests: the live app answers from Neo4j, SQLite fallback.

The chain served from Neo4j must be byte-identical to the SQLite
chain — same best match, confidence, answer text, evidence records
in the same order, same timeline — or the fallback is lying about
the source. Live tests need NEO4J_URI / NEO4J_USERNAME /
NEO4J_PASSWORD in the environment (the Aura instance credentials,
never written into a file) and skip when they are unset, so the
suite stays green anywhere. Fallback and marker tests need no
credentials. Run: python3 -m pytest tests/ -q
"""
import os

import pytest

import app as ui_app
from whycode.graph import GraphStore
from whycode.neo4j_chain import Neo4jGraphStore, store_from_env
from whycode.qa import ask, decision_timeline

Q1 = "Why does ignore_warnings match substrings by default?"
STEERING = "Why does Django need a steering council?"
FORK = "Why didn't Django fork instead of adding async?"
MICRO = "Why does Django use microservices?"

LIVE = bool(os.environ.get("NEO4J_URI")
            and os.environ.get("NEO4J_USERNAME")
            and os.environ.get("NEO4J_PASSWORD"))
needs_live = pytest.mark.skipif(not LIVE, reason="NEO4J_* env vars not set")


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


def _assert_same_answer(sqlite_store, neo4j_store, question):
    a = ask(sqlite_store, question)
    b = ask(neo4j_store, question)
    assert a == b, f"Neo4j answer differs from SQLite for {question!r}"
    if not a.get("refused"):
        assert decision_timeline(sqlite_store, a["match"], a["evidence"]) == \
            decision_timeline(neo4j_store, b["match"], b["evidence"])


# --- Live parity: Neo4j chain == SQLite chain ------------------------------

@needs_live
def test_neo4j_chain_matches_sqlite_q1(neo4j_store):
    _assert_same_answer(GraphStore("data/whycode.db"), neo4j_store, Q1)


@needs_live
def test_neo4j_chain_matches_sqlite_steering(neo4j_store):
    sq = GraphStore("data/whycode.db")
    _assert_same_answer(sq, neo4j_store, STEERING)
    # The superseded banner must still fire from Neo4j: the outgoing
    # supersedes edge is what the banner reads.
    assert "superseded by: DEP 0019" in ask(neo4j_store, STEERING)["answer"]


@needs_live
def test_neo4j_why_not_and_refusal_match_sqlite(neo4j_store):
    sq = GraphStore("data/whycode.db")
    _assert_same_answer(sq, neo4j_store, FORK)
    _assert_same_answer(sq, neo4j_store, MICRO)


# --- Fallback: Neo4j down -> SQLite, still an answer -----------------------

def test_neo4j_store_raises_on_dead_uri():
    with pytest.raises(Exception):
        Neo4jGraphStore("neo4j+s://127.0.0.1:9", "x", "x")


def test_app_falls_back_to_sqlite_on_dead_uri(client, monkeypatch):
    monkeypatch.setenv("NEO4J_URI", "neo4j+s://127.0.0.1:9")
    monkeypatch.setenv("NEO4J_USERNAME", "x")
    monkeypatch.setenv("NEO4J_PASSWORD", "x")
    r = client.get("/", query_string={"q": Q1})
    assert r.status_code == 200
    assert b"<!-- chain-source: sqlite -->" in r.data
    assert b"99%" in r.data
    assert b"3 linked record" in r.data


def test_app_serves_sqlite_when_neo4j_not_configured(client, monkeypatch):
    monkeypatch.delenv("NEO4J_URI", raising=False)
    monkeypatch.delenv("NEO4J_USERNAME", raising=False)
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
    r = client.get("/", query_string={"q": Q1})
    assert r.status_code == 200
    assert b"<!-- chain-source: sqlite -->" in r.data
    assert b"99%" in r.data


# --- Chain-source marker ----------------------------------------------------

@needs_live
def test_chain_source_marker_neo4j_when_live(client):
    r = client.get("/", query_string={"q": Q1})
    assert r.status_code == 200
    assert b"<!-- chain-source: neo4j -->" in r.data
    assert b"99%" in r.data
    assert b"3 linked record" in r.data


@needs_live
def test_chain_source_marker_neo4j_steering_banner(client):
    r = client.get("/", query_string={"q": STEERING})
    assert r.status_code == 200
    assert b"<!-- chain-source: neo4j -->" in r.data
    assert b"Superseded decision" in r.data
    assert b"DEP 0019" in r.data
