#!/usr/bin/env python3
"""WhyCode MCP Server Launcher.

Usage:
    python whycode_mcp.py

Can be configured in Cursor, Claude Desktop, Antigravity, and VS Code.
"""
import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from whycode.mcp_server import main

if __name__ == "__main__":
    main()
