# WhyCode Agent Configuration Specification

> **For AI Agents:** You have been instructed to connect and configure the **WhyCode Decision Intelligence MCP Server** in this developer environment. Follow the steps below to configure your IDE and register the tools.

---

## 1. Environment Detection & Configuration

Detect which editor or environment the developer is running, and register the MCP server:

### Option A: Cursor IDE (`.cursor/mcp.json`)
If the workspace has `.cursor/` or the user is in Cursor, write or update `.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "whycode": {
      "command": "python",
      "args": ["whycode_mcp.py"]
    }
  }
}
```

### Option B: Claude Desktop (`claude_desktop_config.json`)
If running in Claude Desktop, add to the `mcpServers` object in the user's config:
```json
{
  "mcpServers": {
    "whycode": {
      "command": "python",
      "args": ["<absolute-path-to-workspace>/whycode_mcp.py"]
    }
  }
}
```

### Option C: VS Code / Continue (`.vscode/settings.json`)
Add to `.vscode/settings.json`:
```json
{
  "mcp": {
    "servers": {
      "whycode": {
        "type": "stdio",
        "command": "python",
        "args": ["whycode_mcp.py"]
      }
    }
  }
}
```

---

## 2. Tools Available After Connection

Once connected, you have direct access to WhyCode's in-memory decision graph:

| Tool | Purpose |
|---|---|
| `whycode_ask(question, repo)` | Ask why a function, architecture, or design choice exists. Returns grounded author rationale, PR links, and System 1 conformal confidence (12 µs). Refuses if ungrounded. |
| `whycode_ingest_repo(repo_path_or_url)` | Ingest any public GitHub repo into the graph on the fly. |
| `whycode_get_entity(entity_id, repo)` | Retrieve full PR/commit body and 2-hop relations (`authored`, `touches`, `supersedes`). |
| `whycode_list_repos()` | List indexed repositories (`django/django`, `psf/requests`, etc.). |
| `whycode_telemetry()` | Inspect System 1 Conformal Gate coverage (99.1%) and latency. |

---

## 3. Recommended Agent Behavior

Whenever the user asks you to:
* Refactor existing code or deprecate a pattern.
* Explain non-obvious architecture (e.g. why an `EXISTS` subquery or in-RAM index is used).
* Review a Pull Request for architectural compliance.

**Do NOT guess or hallucinate.**  
Call `whycode_ask` first to ground your advice in actual repository decision history.

---

## 4. Confirmation Message to Developer

After adding the configuration, reply to the developer:
> *"✓ WhyCode Decision Intelligence is configured and active! I can now query your repository's grounded architectural rationale and commit history via MCP."*
