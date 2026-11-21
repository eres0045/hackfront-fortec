"""Bring-your-own-repo tests: URL validation, ingest from a local
fixture repo (both transports), the QA engine + features on an
ingested repo, the registry cap, and the Flask /ingest route.

No network: the fixture repo is built with the local git CLI and
ingested by path. Run: python3 -m pytest tests/ -q
"""
import os
import subprocess

import pytest

import app as ui_app
from whycode import byo
from whycode.features import (blast_radius, decision_freshness,
                              decision_health, digest, load_bearing)
from whycode.graph import GraphStore
from whycode.qa import ask

Q1 = "Why does ignore_warnings match substrings by default?"


def make_fixture_repo(path, name="fixture"):
    """A tiny local repo: 3 commits, 2 authors, 3 files."""
    os.makedirs(path, exist_ok=True)

    def run(*args, **kw):
        subprocess.run(["git", *args], cwd=path, check=True,
                       capture_output=True, text=True, **kw)

    run("init", "-q")
    run("config", "user.name", "Alice")
    run("config", "user.email", "alice@example.com")
    (path / "README.md").write_text("# Fixture\n")
    (path / "src").mkdir(exist_ok=True)
    (path / "src" / "main.py").write_text("def main():\n    pass\n")
    run("add", ".")
    run("commit", "-q", "-m", "Add main entry point with retry logic")
    run("config", "user.name", "Bob")
    run("config", "user.email", "bob@example.com")
    (path / "src" / "main.py").write_text(
        "def main():\n    backoff = 2\n    pass\n")
    run("add", ".")
    run("commit", "-q", "-m", "Fix retry backoff in main entry point")
    run("config", "user.name", "Alice")
    run("config", "user.email", "alice@example.com")
    (path / "src" / "utils.py").write_text("def parse():\n    pass\n")
    run("add", ".")
    run("commit", "-q", "-m", "Add utils helper for config parsing")
    return path


@pytest.fixture()
def repos_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("WHYCODE_REPOS_DIR", str(tmp_path / "repos"))
    byo.reset_repos_dir_cache()
    yield tmp_path / "repos"
    byo.reset_repos_dir_cache()


@pytest.fixture()
def client():
    ui_app.app.config["TESTING"] = True
    with ui_app.app.test_client() as c:
        yield c


def test_parse_github_url_valid():
    assert byo.parse_github_url(
        "https://github.com/octocat/Hello-World") == (
        "octocat", "Hello-World")
    assert byo.parse_github_url(
        "https://github.com/octocat/Hello-World/") == (
        "octocat", "Hello-World")
    assert byo.parse_github_url(
        "https://github.com/octocat/Hello-World.git") == (
        "octocat", "Hello-World")
    assert byo.parse_github_url(
        "https://github.com/psf/requests") == ("psf", "requests")


def test_parse_github_url_rejects():
    bad = [
        "", None, "not a url",
        "http://github.com/octocat/Hello-World",  # http, not https
        "git@github.com:octocat/Hello-World.git",  # ssh
        "https://gitlab.com/octocat/Hello-World",  # wrong host
        "https://github.com/octocat",  # no repo
        "https://github.com/octocat/Hello-World/issues",  # extra path
        "https://github.com/octocat/Hello-World.git/extra",
        "https://github.com//Hello-World",
        "https://github.com/octocat/Hello World",  # space
        "https://evilgithub.com/octocat/Hello-World",
    ]
    for url in bad:
        assert byo.parse_github_url(url) is None, url


@pytest.mark.parametrize("transport", ["git", "dulwich"])
def test_ingest_fixture_both_transports(tmp_path, repos_dir, transport):
    fixture = make_fixture_repo(tmp_path / "fixture")
    stats = byo.ingest_repo("fixture", "repo", url=str(fixture),
                            transport=transport)
    assert stats["commits"] == 3
    # 3 commits + 3 files + 2 people = 8 entities.
    assert stats["entities"] == 8
    store = GraphStore(byo.repo_db_path("fixture", "repo"))
    kinds = sorted(e["kind"] for e in store.all_entities())
    assert kinds == ["commit", "commit", "commit", "file", "file",
                     "file", "person", "person"]
    edges = {(e["relation"]) for e in store.all_edges()}
    assert edges == {"authored", "touches"}
    # The engine answers a question about this repo from real commits.
    res = ask(store, "Why does main entry point use retry logic?")
    assert not res["refused"]
    assert res["confidence"] == 0.99
    assert res["match"]["kind"] == "commit"
    assert len(res["evidence"]) >= 2  # author + files
    # And refuses honestly when there is no evidence.
    res2 = ask(store, "Why does the database use sharding?")
    assert res2["refused"]


def test_ingest_features_on_byo_repo(tmp_path, repos_dir):
    fixture = make_fixture_repo(tmp_path / "fixture")
    byo.ingest_repo("fixture", "repo", url=str(fixture), transport="git")
    store = GraphStore(byo.repo_db_path("fixture", "repo"))
    res = ask(store, "Why does main entry point use retry logic?")
    blast = blast_radius(store, res["match"], res["evidence"])
    assert blast["file_count"] >= 1
    assert blast["commit_count"] >= 1
    assert blast["people"]  # Alice authored the match
    fresh = decision_freshness(store, res["match"], res["evidence"])
    assert fresh is not None
    assert fresh["line"].startswith("Decided ")
    top = load_bearing(store)
    assert top and all(r["kind"] == "commit" for r in top)
    health = decision_health(store)
    assert health and all(r["kind"] == "commit" for r in health)
    d = digest(store)
    assert d["new_decisions"] == []  # no docs in a history-only graph
    assert d["recent_changes"]  # commits, newest first
    assert d["top_experts"][0]["title"] == "Alice"  # 2 commits


def test_ingest_nonexistent_repo_errors(tmp_path, repos_dir):
    with pytest.raises(byo.IngestError):
        byo.ingest_repo("nope", "missing", url=str(tmp_path / "nope"),
                         transport="git")


def test_registry_prunes_to_three(tmp_path, repos_dir):
    fixture = make_fixture_repo(tmp_path / "fixture")
    for i in range(4):
        byo.ingest_repo(f"owner{i}", "repo", url=str(fixture),
                         transport="git")
    entries = byo._load_registry()
    assert len(entries) == 3
    assert not os.path.exists(byo.repo_db_path("owner0", "repo"))
    assert os.path.exists(byo.repo_db_path("owner3", "repo"))


def test_ingest_rate_limit():
    ui_app.reset_ingest_limits()
    ip = "203.0.113.99"
    for _ in range(5):
        assert ui_app._ingest_allowed(ip)
    assert not ui_app._ingest_allowed(ip)
    ui_app.reset_ingest_limits()


def test_home_shows_byo_card_and_django_still_works(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Try your own repo" in r.data
    assert b"Ingest repo" in r.data
    assert b"repo_url" in r.data
    r = client.post("/", data={"question": Q1})
    assert r.status_code == 200
    assert b"99%" in r.data


def test_ingest_route_rejects_bad_url(client):
    r = client.post("/ingest", data={
        "repo_url": "https://gitlab.com/octocat/Hello-World"})
    assert r.status_code == 200
    assert b"doesn" in r.data and b"public GitHub repo URL" in r.data


def test_ingest_route_sets_cookie_on_success(client, monkeypatch):
    def fake_ingest(owner, repo):
        return {"owner": owner, "repo": repo, "commits": 3, "entities": 8}

    monkeypatch.setattr(byo, "ingest_repo", fake_ingest)
    ui_app.reset_ingest_limits()
    r = client.post("/ingest", data={
        "repo_url": "https://github.com/octocat/Hello-World"})
    assert r.status_code == 302
    assert r.headers["Location"] == "/?repo=octocat/Hello-World"
    assert "whycode_repo=octocat/Hello-World" in r.headers["Set-Cookie"]


def test_unknown_repo_falls_back_to_django(client):
    r = client.get("/?repo=ghost/repo")
    assert r.status_code == 200
    assert b"django/django" in r.data


def test_byo_repo_flow_via_client(tmp_path, repos_dir, client):
    fixture = make_fixture_repo(tmp_path / "fixture")
    byo.ingest_repo("fixture", "repo", url=str(fixture), transport="git")
    r = client.get("/?repo=fixture/repo")
    assert r.status_code == 200
    assert b"fixture/repo" in r.data
    assert b"Back to the Django demo" in r.data
    r = client.post("/", data={
        "question": "Why does main entry point use retry logic?",
        "repo": "fixture/repo"})
    assert r.status_code == 200
    assert b"99%" in r.data
    assert b"chain-source: sqlite" in r.data
    for page in ("/decisions", "/health", "/digest"):
        r = client.get(f"{page}?repo=fixture/repo")
        assert r.status_code == 200, page
    r = client.get("/repo/clear")
    assert r.status_code == 302
    assert "whycode_repo=django" in r.headers["Set-Cookie"]
