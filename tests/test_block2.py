"""Block-2 tests: real supersedes edges, BM25 ranking, chain cleanup.

Supersedes fixtures are short verbatim excerpts of real Django DEP
text (DEP 0019, DEP 0020, DEP 0011, DEP 0007, DEP 0182) — the
extraction must work on the real RST, not on a cleaned-up imitation.
"""
import os
import shutil
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as ui_app
from whycode.graph import GraphStore
from whycode.qa import ask, bm25_scores, evidence_chain
from whycode.supersedes import extract_supersedes_edges

DEP0019_EXCERPT = """\
:DEP: 0019
:Status: Final
:Created: 2021-01-27

Backwards Compatibility
========================

This document supersedes both DEP 10 and DEP 12.

Reference Implementation
========================

N/A
"""

DEP0020_EXCERPT = """\
:DEP: 0020
:Status: Final
:Created: 2025-06-15

Abstract
========

The first release under this DEP is Django ``2028.0``, replacing what
would otherwise have been Django 7.0. This DEP supersedes DEP 4 and
subsumes the clarifications in `DEP 44`__.
"""

DEP0011_EXCERPT = """\
:DEP: 11
:Status: Superseded
:Created: 2020-06-29

Superseded
==========

DEP 11: Accessibility Team has been superseded by the addition of the
Accessibility Team as a Working Group.
"""

DEP0007_EXCERPT = """\
:DEP: 7
:Status: Final

It supersedes Django's previous, unwritten policy of "no external
dependencies allowed."
"""

DEP0182_EXCERPT = """\
:DEP: 182
:Status: Final

* ``TEMPLATE_DIRS`` configures the filesystem template loader. It's
  superseded by the ``DIRS`` setting in each template backend.
"""


def _dep_store():
    """A store with the DEP entities the excerpts refer to."""
    s = GraphStore()
    for eid, title in [
        ("dep:0004-release-schedule", "DEP 4: Release Schedule"),
        ("dep:0010-new-governance", "DEP 0010: New governance"),
        ("dep:0012-steering-council", "DEP 0012: The Steering Council"),
        ("dep:0019-technical-governance-6x",
         "DEP 0019: Technical governance"),
        ("dep:0020-annual-release-cycle", "DEP 0020: Annual Release Cycle"),
        ("dep:0044-clarify-release-process",
         "DEP 0044: Clarify Release Process"),
        ("dep:0011-accessibility-team", "DEP 11: Accessibility Team"),
        ("dep:0007-dependency-policy", "DEP 7: Dependency Policy"),
        ("dep:0182-multiple-template-engines",
         "DEP 182: Multiple Template Engines"),
    ]:
        s.add_entity(eid, "doc", title, "", "")
    return s


# ---------------------------------------------------------------- job 1

def test_extract_dep0019_supersedes_both():
    s = _dep_store()
    s.add_entity("dep:0019-technical-governance-6x", "doc",
                 "DEP 0019: Technical governance", DEP0019_EXCERPT, "")
    report = extract_supersedes_edges(s)
    assert ("dep:0010-new-governance",
            "dep:0019-technical-governance-6x") in report["added"]
    assert ("dep:0012-steering-council",
            "dep:0019-technical-governance-6x") in report["added"]
    assert not report["skipped"]


def test_extract_dep0020_supersedes_4_but_not_44():
    # "subsumes the clarifications in DEP 44" is not superseding it.
    s = _dep_store()
    s.add_entity("dep:0020-annual-release-cycle", "doc",
                 "DEP 0020: Annual Release Cycle", DEP0020_EXCERPT, "")
    report = extract_supersedes_edges(s)
    assert report["added"] == [("dep:0004-release-schedule",
                                "dep:0020-annual-release-cycle")]
    assert not report["skipped"]


def test_extract_no_edge_for_settings_or_policy_or_working_group():
    s = _dep_store()
    for eid, body in [
        ("dep:0011-accessibility-team", DEP0011_EXCERPT),
        ("dep:0007-dependency-policy", DEP0007_EXCERPT),
        ("dep:0182-multiple-template-engines", DEP0182_EXCERPT),
    ]:
        ent = s.get_entity(eid)
        s.add_entity(eid, "doc", ent["title"], body, "")
    report = extract_supersedes_edges(s)
    assert report["added"] == []
    assert s.conn.execute(
        "SELECT COUNT(*) FROM edges WHERE relation='supersedes'"
    ).fetchone()[0] == 0


def test_extract_ambiguous_number_is_skipped_not_guessed():
    s = GraphStore()
    s.add_entity("dep:0007-dependency-policy", "doc", "DEP 7: A", "", "")
    s.add_entity("dep:0007-official-projects", "doc", "DEP 7: B", "", "")
    s.add_entity("dep:0099-test", "doc", "DEP 99: Test",
                 "This DEP supersedes DEP 7.", "")
    report = extract_supersedes_edges(s)
    assert report["added"] == []
    assert any("DEP 7" in r for r in report["skipped"])
    assert s.conn.execute(
        "SELECT COUNT(*) FROM edges WHERE relation='supersedes'"
    ).fetchone()[0] == 0


def test_extract_missing_target_is_skipped():
    s = GraphStore()
    s.add_entity("dep:0099-test", "doc", "DEP 99: Test",
                 "This DEP supersedes DEP 123.", "")
    report = extract_supersedes_edges(s)
    assert report["added"] == []
    assert any("DEP 123" in r for r in report["skipped"])


def test_extract_is_idempotent():
    s = _dep_store()
    s.add_entity("dep:0019-technical-governance-6x", "doc",
                 "DEP 0019: Technical governance", DEP0019_EXCERPT, "")
    first = extract_supersedes_edges(s)
    second = extract_supersedes_edges(s)
    assert len(first["added"]) == len(second["added"]) == 2
    assert s.conn.execute(
        "SELECT COUNT(*) FROM edges WHERE relation='supersedes'"
    ).fetchone()[0] == 2


def _supersede_store():
    """Old doc D1 superseded by new doc D2; both have chains."""
    s = GraphStore()
    s.add_entity("d1", "doc", "Old governance rules",
                 "The old governance rules for the project.", "u/d1")
    s.add_entity("d2", "doc", "New governance rules",
                 "The new governance rules for the project.", "u/d2")
    s.add_entity("f1", "file", "gov.py", "", "u/f1")
    s.add_entity("f2", "file", "gov2.py", "", "u/f2")
    s.add_edge("d1", "d2", "supersedes")
    s.add_edge("d1", "f1", "mentions")
    s.add_edge("d2", "f2", "mentions")
    return s


def test_superseded_banner_fires_on_old_decision():
    r = ask(_supersede_store(), "why old governance rules?")
    assert not r["refused"]
    assert "superseded" in r["answer"]
    assert "New governance rules" in r["answer"]


def test_newer_decision_is_never_flagged_superseded():
    r = ask(_supersede_store(), "why new governance rules?")
    assert not r["refused"]
    assert "superseded" not in r["answer"]


@pytest.fixture()
def client():
    ui_app.app.config["TESTING"] = True
    with ui_app.app.test_client() as c:
        yield c


def test_ui_banner_fires_on_real_dep_edges(client, tmp_path):
    test_db = tmp_path / "test.db"
    shutil.copy("data/whycode.db", test_db)
    store = GraphStore(str(test_db))
    report = extract_supersedes_edges(store)
    assert len(report["added"]) == 3
    old = ui_app.DB_PATH
    ui_app.DB_PATH = str(test_db)
    try:
        r = client.post(
            "/", data={"question": "Why does Django need a steering council?"})
    finally:
        ui_app.DB_PATH = old
    assert r.status_code == 200
    assert b"Superseded decision" in r.data
    assert b"DEP 0019" in r.data


# ---------------------------------------------------------------- job 2

def test_bm25_title_term_beats_body_repetition():
    # A has both terms in its title; B repeats both terms 3x in a long
    # body. Both match 2/2, so coverage cannot decide it — title
    # weighting (2x) must make A win.
    s = GraphStore()
    s.add_entity("a", "doc", "Zebra routing", "", "u/a")
    s.add_entity("b", "doc", "Other notes",
                 "zebra routing zebra routing zebra routing "
                 + "filler " * 12, "u/b")
    s.add_entity("fa", "file", "a.py", "", "u/fa")
    s.add_entity("fb", "file", "b.py", "", "u/fb")
    s.add_edge("a", "fa", "mentions")
    s.add_edge("b", "fb", "mentions")
    r = ask(s, "why zebra routing?")
    assert not r["refused"]
    assert r["match"]["id"] == "a"


def test_bm25_partial_coverage_never_beats_full_coverage():
    # R matches only the rare term (huge IDF); F matches both common
    # terms. Coverage is the gate: F must win, or a 1-term match with a
    # chain would answer a question its other terms say nothing about.
    s = GraphStore()
    s.add_entity("r", "doc", "Quasiflobber notes", "", "u/r")
    s.add_entity("f", "doc", "Python compatibility guide",
                 "python compatibility", "u/f")
    s.add_entity("fr", "file", "r.py", "", "u/fr")
    s.add_entity("ff", "file", "f.py", "", "u/ff")
    s.add_edge("r", "fr", "mentions")
    s.add_edge("f", "ff", "mentions")
    r = ask(s, "why python compatibility quasiflobber?")
    assert not r["refused"]
    assert r["match"]["id"] == "f"


def test_bm25_scores_title_weighted():
    s = GraphStore()
    s.add_entity("a", "doc", "Zebra routing", "", "u/a")
    s.add_entity("b", "doc", "Other notes",
                 "zebra routing zebra routing zebra routing "
                 + "filler " * 12, "u/b")
    scores = bm25_scores(s, ["zebra", "routing"])
    assert scores["a"] > scores["b"]


def test_real_db_q1_still_099_with_clean_chain():
    store = GraphStore("data/whycode.db")
    r = ask(store, "Why does ignore_warnings match substrings by default?")
    assert not r["refused"]
    assert r["confidence"] == 0.99
    assert r["match"]["id"] == "commit:2d9d619676e2"
    assert {e["id"] for e in r["evidence"]} == {
        "issue:37089", "person:HelmiDev03", "commit:8aab4fa1ab45"}


def test_real_db_q1_task_wording_still_099():
    store = GraphStore("data/whycode.db")
    r = ask(store, "Why was ignore_warnings added?")
    assert not r["refused"]
    assert r["confidence"] == 0.99
    assert {e["id"] for e in r["evidence"]} == {
        "issue:37089", "person:HelmiDev03", "commit:2d9d619676e2"}


def test_real_db_py315_ticket_still_beats_mailers_dep():
    store = GraphStore("data/whycode.db")
    r = ask(store, "Why is Python 3.15 compatibility being added?")
    assert not r["refused"]
    assert r["confidence"] == 0.99
    assert r["match"]["kind"] == "issue"
    assert "Python 3.15 compatibility" in r["match"]["title"]


def test_real_db_microservices_still_refuses():
    store = GraphStore("data/whycode.db")
    r = ask(store, "Why does Django use microservices?")
    assert r["refused"]
    assert "DEP 0009" in r["reason"]


# ---------------------------------------------------------------- job 3

def _noisy_chain_store():
    """Q1's shape: match commit fixes a ticket; its author also wrote
    an unrelated commit and PR. The chain must hold the ticket and the
    author, not the author's other work, and not the match itself."""
    s = GraphStore()
    s.add_entity("c1", "commit", "Fix widget rendering in forms",
                 "Fixes the widget. widget forms.", "u/c1")
    s.add_entity("t1", "issue", "Widget rendering broken",
                 "Widget rendering is broken in forms.", "u/t1")
    s.add_entity("p1", "person", "Author One", "", "u/p1")
    s.add_entity("c2", "commit", "Unrelated CI tweak",
                 "CI tweak, nothing to do with widgets.", "u/c2")
    s.add_entity("pr9", "pr", "Unrelated docs fix",
                 "Docs fix by the same author.", "u/pr9")
    s.add_edge("c1", "t1", "fixes")
    s.add_edge("c1", "p1", "authored")
    s.add_edge("c2", "p1", "authored")
    s.add_edge("pr9", "p1", "authored")
    s.add_edge("c1", "t1", "references")
    return s


def test_chain_excludes_same_author_noise():
    s = _noisy_chain_store()
    ids = {e["id"] for e in evidence_chain(s, "c1")}
    assert ids == {"t1", "p1"}
    assert "c2" not in ids and "pr9" not in ids


def test_chain_excludes_best_match_itself():
    s = _noisy_chain_store()
    ids = [e["id"] for e in evidence_chain(s, "c1")]
    assert "c1" not in ids
    assert len(ids) == len(set(ids))


def test_chain_dedupes_entity_reached_by_two_relations():
    # c1 reaches t1 by both fixes and references: t1 appears once.
    s = _noisy_chain_store()
    chain = evidence_chain(s, "c1")
    assert [e["id"] for e in chain].count("t1") == 1
