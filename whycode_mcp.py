#!/usr/bin/env python3
"""WhyCode MCP server launcher (stdio).

Runs the same FastMCP server the hosted service exposes over HTTP
(whycode/mcp_server.py — tools why_code, blast_radius, who_knows,
decision_health), over stdio, so Cursor, Claude Desktop, VS Code and
other MCP clients can use it from a local checkout.

Usage:
    python whycode_mcp.py

Configure in Cursor (.cursor/mcp.json) or Claude Desktop
(claude_desktop_config.json) with the path to this file. The server
needs the MCP dependencies (see requirements-mcp.txt) and reads the
bundled SQLite graph by default; set NEO4J_* env vars to serve from
Neo4j, exactly like the hosted service.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from whycode.mcp_server import mcp

if __name__ == "__main__":
    mcp.run()
