"""Tests for the GitHub PR bot (whycode/prbot.py + /github-webhook).

GitHub API calls are monkeypatched — no network, no token. Live
behaviour (real webhook, real PR) is verified by hand on the deploy,
not here. Run: python3 -m pytest tests/ -q
"""
import hashlib
import hmac
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import app as ui_app
from whycode.graph import GraphStore
from whycode import prbot


@pytest.fixture()
def client():
    ui_app.app.config["TESTING"] = True
    with ui_app.app.test_client() as c:
        yield c


def _store_with_decision():
    """django/test/utils.py governed by DEP 0018 (doc) + one commit."""
    s = GraphStore()
    s.add_entity("file:django/test/utils.py", "file",
                 "django/test/utils.py", "", "")
    s.add_entity("dep:0018-mailers", "doc",
                 "DEP 0018: Dictionary-based MAILERS setting",
                 ":Created: 2019-01-01\n\nBody.", "u/d18")
    s.add_entity("c1", "commit", "Fixed #1 -- Touched utils",
                 "touched it", "u/c1", "2020-01-01T00:00:00Z")
    s.add_entity("i1", "issue", "Bug in utils", "", "u/i1")
    s.add_entity("p1", "person", "alice", "", "")
    s.add_edge("dep:0018-mailers", "file:django/test/utils.py", "mentions")
    s.add_edge("c1", "file:django/test/utils.py", "touches")
    s.add_edge("c1", "i1", "fixes")
    s.add_edge("c1", "p1", "authored")
    return s


def test_find_decision_prefers_doc():
    s = _store_with_decision()
    d = prbot.find_decision_for_files(s, ["django/test/utils.py"])
    assert d is not None
    assert d["kind"] == "doc"
    assert "DEP 0018" in d["title"]


def test_find_decision_falls_back_to_commit():
    s = GraphStore()
    s.add_entity("file:a.py", "file", "a.py", "", "")
    s.add_entity("c1", "commit", "Fixed #9 -- Changed a", "", "u/c1",
                 "2020-01-01T00:00:00Z")
    s.add_entity("i9", "issue", "Bug in a", "", "u/i9")
    s.add_edge("c1", "file:a.py", "touches")
    s.add_edge("c1", "i9", "fixes")
    d = prbot.find_decision_for_files(s, ["a.py"])
    assert d["kind"] == "commit"
    assert d["issue"]["id"] == "i9"


def test_find_decision_none_for_unknown_file():
    s = _store_with_decision()
    assert prbot.find_decision_for_files(s, ["no/such.py"]) is None


def test_build_comment_cites_decision_and_blast():
    s = _store_with_decision()
    comment = prbot.build_comment(s, ["django/test/utils.py"])
    assert comment is not None
    assert "DEP 0018" in comment
    assert "Blast radius:" in comment
    assert "alice" in comment
    assert prbot.MARKER in comment


def test_build_comment_none_without_decision():
    s = _store_with_decision()
    assert prbot.build_comment(s, ["other.py"]) is None


def test_signature_verification():
    secret = "s3cr3t"
    body = b'{"a": 1}'
    sig = "sha256=" + hmac.new(
        secret.encode(), body, hashlib.sha256).hexdigest()
    assert prbot.verify_signature(secret, body, sig)
    assert not prbot.verify_signature(secret, body, "sha256=deadbeef")
    assert not prbot.verify_signature(secret, body, "")
    # No secret configured: verification is off (documented).
    assert prbot.verify_signature("", body, "")


class _FakeGitHub:
    """Stand-in for prbot.github_api: records calls, returns canned data."""

    def __init__(self):
        self.posts = []
        self.existing_comments = []

    def __call__(self, token, method, path, json_body=None):
        assert token == "tok"
        if method == "GET" and path.endswith("/pulls/7/files"):
            return 200, [{"filename": "django/test/utils.py"}]
        if method == "GET" and path.endswith("/issues/7/comments"):
            return 200, self.existing_comments
        if method == "POST" and path.endswith("/issues/7/comments"):
            self.posts.append(json_body["body"])
            return 201, {"id": 1}
        raise AssertionError(f"unexpected call {method} {path}")


def test_handle_pr_comments_once(monkeypatch):
    fake = _FakeGitHub()
    monkeypatch.setattr(prbot, "github_api", fake)
    s = _store_with_decision()
    outcome, _ = prbot.handle_pull_request(
        s, "tok", "eres0045/hackfront-fortec", 7)
    assert outcome == "commented"
    assert len(fake.posts) == 1
    assert "DEP 0018" in fake.posts[0]
    # Second run (synchronize): sees its own marker, does not re-post.
    fake.existing_comments = [{"body": fake.posts[0]}]
    outcome, _ = prbot.handle_pull_request(
        s, "tok", "eres0045/hackfront-fortec", 7)
    assert outcome == "already_commented"
    assert len(fake.posts) == 1


def test_handle_pr_silent_without_decision(monkeypatch):
    fake = _FakeGitHub()

    def _files_only(token, method, path, json_body=None):
        if method == "GET" and path.endswith("/pulls/7/files"):
            return 200, [{"filename": "unrelated.py"}]
        raise AssertionError(f"unexpected call {method} {path}")

    monkeypatch.setattr(prbot, "github_api", _files_only)
    s = _store_with_decision()
    outcome, _ = prbot.handle_pull_request(
        s, "tok", "eres0045/hackfront-fortec", 7)
    assert outcome == "no_decision"


def test_webhook_ignores_non_pr_events(client):
    r = client.post("/github-webhook", json={"action": "opened"})
    assert r.status_code == 200
    assert r.get_json()["ignored"] == "not a pull_request event"


def test_webhook_ignores_other_actions(client):
    r = client.post("/github-webhook", json={
        "action": "closed",
        "pull_request": {"number": 1},
        "repository": {"full_name": "x/y"}})
    assert r.status_code == 200
    assert "closed" in r.get_json()["ignored"]


def test_webhook_rejects_bad_signature(client, monkeypatch):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "s3cr3t")
    r = client.post("/github-webhook", json={
        "action": "opened",
        "pull_request": {"number": 1},
        "repository": {"full_name": "x/y"}})
    assert r.status_code == 401


def test_webhook_posts_comment_on_opened_pr(client, monkeypatch):
    fake = _FakeGitHub()
    monkeypatch.setattr(prbot, "github_api", fake)
    monkeypatch.setenv("GITHUB_TOKEN", "tok")
    monkeypatch.delenv("GITHUB_WEBHOOK_SECRET", raising=False)
    r = client.post("/github-webhook", json={
        "action": "opened",
        "pull_request": {"number": 7},
        "repository": {"full_name": "eres0045/hackfront-fortec"}})
    # The app answers from the real bundled DB in tests (SQLite):
    # django/test/utils.py is governed there, so it comments.
    assert r.status_code == 200
    assert r.get_json()["outcome"] == "commented"
    assert len(fake.posts) == 1
