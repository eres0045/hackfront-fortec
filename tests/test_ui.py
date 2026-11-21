"""UI tests: Flask test client against the real bundled DB.

Covers the two demo questions end to end (answer + honest refusal),
empty input, and the superseded banner (on a temp COPY of the DB, never
the real one). Run: python3 -m pytest tests/ -q
"""
import os
import shutil
import tempfile

import pytest

import app as ui_app
from whycode.graph import GraphStore

Q1 = "Why does ignore_warnings match substrings by default?"
Q2 = "Why does Django use microservices?"


@pytest.fixture()
def client():
    ui_app.app.config["TESTING"] = True
    with ui_app.app.test_client() as c:
        yield c


def test_home_renders(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"WhyCode" in r.data
    assert b"ignore_warnings" in r.data  # example question chip


def test_q1_answers_with_evidence(client):
    r = client.post("/", data={"question": Q1})
    assert r.status_code == 200
    assert b"99%" in r.data
    # Chain cleanup (block 2): 3 distinct records — the ticket, the
    # author, the test-coverage commit. The same-author PR 22125 and the
    # best match's duplicate of itself are gone.
    assert b"3 linked record" in r.data
    assert b"22125" not in r.data
    assert b"code.djangoproject.com/ticket/37089" in r.data
    assert b"Evidence graph" in r.data
    assert b"Superseded decision" not in r.data  # Q1's chain has no supersedes edge


def test_q2_refuses_honestly(client):
    r = client.post("/", data={"question": Q2})
    assert r.status_code == 200
    assert b"WhyCode refuses to answer this" in r.data
    assert b"Refusing to invent an answer" in r.data
    assert b"DEP 0009" in r.data
    assert b"Evidence chain" not in r.data


def test_empty_question_does_not_crash(client):
    r = client.post("/", data={"question": "   "})
    assert r.status_code == 200
    assert b"Type a question first" in r.data


def test_superseded_banner_on_test_copy(client, tmp_path, monkeypatch):
    # The banner test mutates a COPY of the SQLite DB, so Neo4j must be
    # out of the picture for it — otherwise the app answers from the
    # live instance (which has no fake edge) and the banner never fires.
    monkeypatch.delenv("NEO4J_URI", raising=False)
    monkeypatch.delenv("NEO4J_USERNAME", raising=False)
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
    test_db = tmp_path / "test.db"
    shutil.copy("data/whycode.db", test_db)
    store = GraphStore(str(test_db))
    store.add_entity("doc:dep:9999-test", "doc", "DEP 9999: Test successor",
                     "", "https://example.com/dep9999")
    store.add_edge("commit:2d9d619676e2", "doc:dep:9999-test", "supersedes")
    old = ui_app.DB_PATH
    ui_app.DB_PATH = str(test_db)
    try:
        r = client.post("/", data={"question": Q1})
    finally:
        ui_app.DB_PATH = old
    assert r.status_code == 200
    assert b"Superseded decision" in r.data
    assert b"DEP 9999: Test successor" in r.data
