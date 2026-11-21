"""WhyCode MCP server — the memory layer for AI coding agents.

An AI agent writing code in a repo has no memory of why anything is
the way it is. This server gives it one: four tools, all computed
from the same django/django history graph the web app answers from
(Neo4j first, SQLite fallback from the bundled DB — the same store
abstraction, the same refusal rules).

Tools:
- why_code(question): the cited answer, with confidence and the
  evidence chain — or an honest refusal when the graph has nothing.
- blast_radius(decision=..., file=...): what breaks if this changes
  — files, commits, issues/PRs, related decisions, who to talk to.
- who_knows(file): the people who authored the commits touching a
  file, ranked by how much they wrote.
- decision_health(): the freshness ranking — every dated decision,
  ranked by how much its code moved since it was made.

Transport is streamable HTTP (the /mcp endpoint), so the server runs
as a normal Render web service: `uvicorn whycode.mcp_server:app`.
No credentials are ever returned in a tool result; the Neo4j
connection details stay server-side environment variables.
"""
import os

from fastmcp import FastMCP

from whycode.features import (
    blast_radius as _blast_radius,
)
from whycode.features import (
    decision_health as _decision_health,
)
from whycode.features import (
    who_to_ask as _who_to_ask,
)
from whycode.graph import GraphStore
from whycode.neo4j_chain import cached_store_from_env
from whycode.qa import ask

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get(
    "WHYCODE_DB", os.path.join(BASE_DIR, "data", "whycode.db"))

mcp = FastMCP("whycode")


def _store():
    """(store, source): Neo4j first, SQLite fallback — same as the app."""
    try:
        neo4j_store = cached_store_from_env()
    except Exception:
        neo4j_store = None
    if neo4j_store is not None:
        return neo4j_store, "neo4j"
    return GraphStore(DB_PATH), "sqlite"


def _person_counts(store, commits):
    """{person title: commits authored} for a set of commit entities."""
    counts = {}
    for commit in commits:
        for nb in store.neighbors(commit["id"], "authored"):
            if nb.get("kind") == "person":
                counts[nb["title"]] = counts.get(nb["title"], 0) + 1
    return sorted(
        ({"name": name, "commits": n} for name, n in counts.items()),
        key=lambda p: (-p["commits"], p["name"]))


@mcp.tool()
def why_code(question: str) -> dict:
    """Ask why the Django code is like this.

    Returns the cited answer with confidence and the evidence chain
    (each record links to its commit, PR, ticket or DEP), or an
    honest refusal when the graph holds no evidence for the question.
    """
    store, source = _store()
    result = ask(store, question)
    if result.get("refused"):
        return {"refused": True, "reason": result["reason"],
                "confidence": result["confidence"], "source": source}
    return {
        "refused": False,
        "answer": result["answer"],
        "confidence": result["confidence"],
        "best_match": {
            "id": result["match"]["id"],
            "title": result["match"]["title"],
            "kind": result["match"]["kind"],
            "url": result["match"].get("url") or "",
        },
        "evidence": [
            {"id": e["id"], "title": e["title"], "kind": e["kind"],
             "relation": e["relation"], "url": e.get("url") or ""}
            for e in result["evidence"]
        ],
        "source": source,
    }


@mcp.tool()
def blast_radius(decision: str = "", file: str = "") -> dict:
    """What breaks if I change this?

    Give either a decision as a question (e.g. "Why does Django need
    a steering council?") or a repo file path (e.g.
    "django/test/utils.py"). Returns the files, commits, issues/PRs
    and related decisions in the radius, plus who to talk to first.
    """
    store, source = _store()
    if file:
        path = file[5:] if file.startswith("file:") else file
        match = store.get_entity(f"file:{path}")
        if not match:
            return {"refused": True,
                    "reason": f"No file {path} in the graph.",
                    "source": source}
        evidence = []
    elif decision:
        result = ask(store, decision)
        if result.get("refused"):
            return {"refused": True, "reason": result["reason"],
                    "confidence": result["confidence"], "source": source}
        match = result["match"]
        evidence = result["evidence"]
    else:
        return {"refused": True,
                "reason": "Give a decision question or a file path.",
                "source": source}
    blast = _blast_radius(store, match, evidence)
    return {
        "refused": False,
        "decision": {"id": match["id"], "title": match["title"],
                     "kind": match["kind"]},
        "file_count": blast["file_count"],
        "commit_count": blast["commit_count"],
        "issue_count": blast["issue_count"],
        "decision_count": blast["decision_count"],
        "files": [f["id"][5:] for f in blast["files"]],
        "commits": [{"id": c["id"], "title": c["title"],
                     "url": c.get("url") or "",
                     "created_at": c.get("created_at") or ""}
                    for c in blast["commits"]],
        "issues": [{"id": i["id"], "title": i["title"], "kind": i["kind"],
                    "url": i.get("url") or ""} for i in blast["issues"]],
        "decisions": [{"id": d["id"], "title": d["title"],
                       "url": d.get("url") or ""}
                      for d in blast["decisions"]],
        "talk_to": _who_to_ask(blast),
        "source": source,
    }


@mcp.tool()
def who_knows(file: str) -> dict:
    """Who knows this file? Top authors of the commits touching it.

    Give a repo path like "django/test/utils.py". Returns people
    ranked by how many commits touching the file they authored.
    """
    store, source = _store()
    path = file[5:] if file.startswith("file:") else file
    match = store.get_entity(f"file:{path}")
    if not match:
        return {"refused": True,
                "reason": f"No file {path} in the graph.",
                "source": source}
    commits = []
    for nb in store.neighbors_reverse(match["id"]):
        if nb.get("kind") == "commit" and nb.get("relation") == "touches":
            commits.append(nb)
    return {"refused": False, "file": path,
            "commits_touching": len(commits),
            "people": _person_counts(store, commits)[:5],
            "source": source}


@mcp.tool()
def decision_health() -> dict:
    """Which decisions has the code outgrown?

    Every dated decision ranked by how much its code moved since it
    was made (churn = commits after the decision date touching its
    files). Facts only — no verdict on whether a decision is stale.
    """
    store, source = _store()
    return {"refused": False,
            "decisions": _decision_health(store),
            "source": source}


# ASGI app for uvicorn / Render: streamable HTTP on /mcp.
app = mcp.http_app()


if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0",
            port=int(os.environ.get("PORT", "8000")))
