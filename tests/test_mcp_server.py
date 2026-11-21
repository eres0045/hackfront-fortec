"""Tests for the WhyCode MCP server (FastMCP, streamable HTTP).

The tools are exercised through FastMCP's in-memory client — the
real MCP protocol path, no network. Live tests (Neo4j source) run
only when NEO4J_* env vars are set. Run: python3 -m pytest tests/ -q
"""
import asyncio
import os

import pytest
from fastmcp import Client

from whycode.mcp_server import mcp

LIVE = bool(os.environ.get("NEO4J_URI")
            and os.environ.get("NEO4J_USERNAME")
            and os.environ.get("NEO4J_PASSWORD"))
needs_live = pytest.mark.skipif(not LIVE, reason="NEO4J_* env vars not set")


def _run(coro):
    return asyncio.run(coro)


async def _list_tools():
    async with Client(mcp) as client:
        return await client.list_tools()


async def _call(name, args):
    async with Client(mcp) as client:
        return await client.call_tool(name, args)


def test_mcp_lists_exactly_four_tools():
    tools = _run(_list_tools())
    assert sorted(t.name for t in tools) == [
        "blast_radius", "decision_health", "who_knows", "why_code",
    ]


def test_why_code_answers_with_citation():
    result = _run(_call("why_code", {
        "question": "Why does ignore_warnings match substrings by "
                    "default?"}))
    assert not result.data["refused"]
    assert result.data["confidence"] == 0.99
    assert len(result.data["evidence"]) == 3
    assert result.data["best_match"]["id"] == "commit:2d9d619676e2"
    assert result.data["source"] in ("neo4j", "sqlite")


def test_why_code_refuses_honestly():
    result = _run(_call("why_code", {
        "question": "Why does Django use microservices?"}))
    assert result.data["refused"]
    assert "Refusing to invent" in result.data["reason"]


def test_blast_radius_by_decision_and_by_file():
    by_decision = _run(_call("blast_radius", {
        "decision": "Why does ignore_warnings match substrings by "
                    "default?"}))
    assert not by_decision.data["refused"]
    assert by_decision.data["commit_count"] == 2
    assert by_decision.data["talk_to"][0]["title"] == "HelmiDev03"
    by_file = _run(_call("blast_radius", {
        "file": "django/test/utils.py"}))
    assert not by_file.data["refused"]
    assert by_file.data["file_count"] >= 1
    assert by_file.data["commit_count"] >= 1


def test_blast_radius_needs_an_argument():
    result = _run(_call("blast_radius", {}))
    assert result.data["refused"]


def test_blast_radius_unknown_file_refuses():
    result = _run(_call("blast_radius", {"file": "no/such/file.py"}))
    assert result.data["refused"]


def test_who_knows_ranks_authors():
    result = _run(_call("who_knows", {"file": "django/test/utils.py"}))
    assert not result.data["refused"]
    assert result.data["commits_touching"] >= 1
    assert result.data["people"]
    counts = [p["commits"] for p in result.data["people"]]
    assert counts == sorted(counts, reverse=True)


def test_decision_health_returns_ranked_list():
    result = _run(_call("decision_health", {}))
    assert not result.data["refused"]
    rows = result.data["decisions"]
    assert len(rows) == 10
    churns = [r["churn"] for r in rows]
    assert churns == sorted(churns, reverse=True)
    assert rows[0]["id"] == "dep:0020-annual-release-cycle"


@needs_live
def test_live_why_code_served_from_neo4j():
    result = _run(_call("why_code", {
        "question": "Why does ignore_warnings match substrings by "
                    "default?"}))
    assert result.data["source"] == "neo4j"
    assert result.data["confidence"] == 0.99
