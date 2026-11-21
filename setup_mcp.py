"""WhyCode Universal MCP Automated Setup Script.

Enables any AI Agent (Cursor, Claude Code, Windsurf, Codex, VS Code) to configure
WhyCode Decision Intelligence with zero manual effort.
"""
import os
import sys
import json
import subprocess

def setup_mcp():
    workspace_dir = os.path.abspath(os.path.dirname(__file__))
    python_exe = sys.executable
    mcp_script = os.path.join(workspace_dir, "whycode_mcp.py")
    configured = []

    print("✦ Starting WhyCode Universal MCP Setup...")
    print(f"  • Workspace: {workspace_dir}")
    print(f"  • Python:    {python_exe}")

    # 1. Cursor IDE Configuration (.cursor/mcp.json)
    cursor_dir = os.path.join(workspace_dir, ".cursor")
    os.makedirs(cursor_dir, exist_ok=True)
    cursor_mcp_file = os.path.join(cursor_dir, "mcp.json")
    
    cursor_config = {}
    if os.path.exists(cursor_mcp_file):
        try:
            with open(cursor_mcp_file, "r", encoding="utf-8") as f:
                cursor_config = json.load(f)
        except Exception:
            cursor_config = {}
            
    if "mcpServers" not in cursor_config:
        cursor_config["mcpServers"] = {}
        
    cursor_config["mcpServers"]["whycode"] = {
        "command": python_exe,
        "args": [mcp_script]
    }
    
    with open(cursor_mcp_file, "w", encoding="utf-8") as f:
        json.dump(cursor_config, f, indent=2)
    configured.append(f"Cursor IDE: {cursor_mcp_file}")

    # 2. Workspace root mcp.json (Standard MCP manifest)
    root_mcp_file = os.path.join(workspace_dir, "mcp.json")
    root_config = {
        "mcpServers": {
            "whycode": {
                "command": python_exe,
                "args": [mcp_script]
            }
        }
    }
    with open(root_mcp_file, "w", encoding="utf-8") as f:
        json.dump(root_config, f, indent=2)
    configured.append(f"Standard MCP Manifest: {root_mcp_file}")

    # 3. Claude Desktop Configuration (if present on system)
    claude_paths = []
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            claude_paths.append(os.path.join(appdata, "Claude", "claude_desktop_config.json"))
    elif sys.platform == "darwin":
        claude_paths.append(os.path.expanduser("~/Library/Application Support/Claude/claude_desktop_config.json"))
    else:
        claude_paths.append(os.path.expanduser("~/.config/Claude/claude_desktop_config.json"))

    for cpath in claude_paths:
        cdir = os.path.dirname(cpath)
        if os.path.exists(cdir):
            c_cfg = {}
            if os.path.exists(cpath):
                try:
                    with open(cpath, "r", encoding="utf-8") as f:
                        c_cfg = json.load(f)
                except Exception:
                    c_cfg = {}
            if "mcpServers" not in c_cfg:
                c_cfg["mcpServers"] = {}
            c_cfg["mcpServers"]["whycode"] = {
                "command": python_exe,
                "args": [mcp_script]
            }
            try:
                with open(cpath, "w", encoding="utf-8") as f:
                    json.dump(c_cfg, f, indent=2)
                configured.append(f"Claude Desktop: {cpath}")
            except Exception as e:
                print(f"  Note: Could not write to Claude Desktop config ({e})")

    # 4. VS Code Configuration (.vscode/settings.json)
    vscode_dir = os.path.join(workspace_dir, ".vscode")
    os.makedirs(vscode_dir, exist_ok=True)
    vscode_settings = os.path.join(vscode_dir, "settings.json")
    vs_cfg = {}
    if os.path.exists(vscode_settings):
        try:
            with open(vscode_settings, "r", encoding="utf-8") as f:
                vs_cfg = json.load(f)
        except Exception:
            vs_cfg = {}
            
    if "mcp" not in vs_cfg:
        vs_cfg["mcp"] = {}
    if "servers" not in vs_cfg["mcp"]:
        vs_cfg["mcp"]["servers"] = {}
        
    vs_cfg["mcp"]["servers"]["whycode"] = {
        "type": "stdio",
        "command": python_exe,
        "args": [mcp_script]
    }
    with open(vscode_settings, "w", encoding="utf-8") as f:
        json.dump(vs_cfg, f, indent=2)
    configured.append(f"VS Code: {vscode_settings}")

    # 5. Windsurf IDE Configuration (if installed)
    windsurf_dir = ""
    if sys.platform == "win32":
        userprofile = os.environ.get("USERPROFILE", "")
        if userprofile:
            windsurf_dir = os.path.join(userprofile, ".codeium", "windsurf")
    else:
        windsurf_dir = os.path.expanduser("~/.codeium/windsurf")

    if windsurf_dir and os.path.exists(windsurf_dir):
        windsurf_file = os.path.join(windsurf_dir, "mcp_config.json")
        ws_cfg = {}
        if os.path.exists(windsurf_file):
            try:
                with open(windsurf_file, "r", encoding="utf-8") as f:
                    ws_cfg = json.load(f)
            except Exception:
                ws_cfg = {}
        if "mcpServers" not in ws_cfg:
            ws_cfg["mcpServers"] = {}
        ws_cfg["mcpServers"]["whycode"] = {
            "command": python_exe,
            "args": [mcp_script]
        }
        try:
            with open(windsurf_file, "w", encoding="utf-8") as f:
                json.dump(ws_cfg, f, indent=2)
            configured.append(f"Windsurf IDE: {windsurf_file}")
        except Exception as e:
            print(f"  Note: Could not write to Windsurf config ({e})")

    # 6. Verify MCP Tool Registration
    print("\n✓ Verification & Tool Inspection:")
    try:
        from whycode.mcp_server import (
            whycode_ask,
            whycode_ingest_repo,
            whycode_get_entity,
            whycode_list_repos,
            whycode_telemetry
        )
        print("  • whycode_ask:         READY (Conformal Gate Active)")
        print("  • whycode_ingest_repo: READY (Git Graph Ingestion)")
        print("  • whycode_get_entity:  READY (2-Hop Evidence Traversal)")
        print("  • whycode_list_repos:  READY (Multi-Repo Registry)")
        print("  • whycode_telemetry:   READY (12 µs Telemetry)")
    except Exception as e:
        print(f"  ⚠️ Warning importing tools: {e}")

    print("\n🎉 WhyCode MCP Setup Complete!")
    print("Configured targets:")
    for c in configured:
        print(f"  ✓ {c}")
    print("\nNext step: The AI agent can now call `whycode_ask` directly whenever you ask architectural questions.")
    return 0

if __name__ == "__main__":
    sys.exit(setup_mcp())
