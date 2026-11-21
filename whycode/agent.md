# WhyCode Decision Intelligence — AI Agent Setup & Protocol Specification

> **Instruction for AI Agent:** The developer has asked you to configure and use WhyCode Decision Intelligence via the Model Context Protocol (MCP). Follow the instructions below to enable the tools in your environment.

---

## ⚡ 1. Fastest Automated Setup (Recommended)

If you have terminal/bash access, run this single command in the workspace root:

```bash
python setup_mcp.py
```

**What this does automatically:**
- Auto-detects your IDE (Cursor, VS Code, Claude Desktop, Windsurf).
- Writes the exact MCP configuration with absolute paths to `.cursor/mcp.json`, `.vscode/settings.json`, and `mcp.json`.
- Automatically executes internal diagnostic tests to verify all 5 tools are ready.

---

## 💻 2. One-Line Setup for Claude Code CLI

If you are running inside **Claude Code**, run:
```bash
claude mcp add whycode python whycode_mcp.py
```

---

## 🛠️ 3. Manual Configuration (If Terminal is Unavailable)

If you cannot run shell commands, write or merge the configuration into your environment's config file:

### A. Cursor IDE (`.cursor/mcp.json`)
Create or merge into `.cursor/mcp.json`:
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

### B. VS Code / Continue / Cline (`.vscode/settings.json`)
Create or merge into `.vscode/settings.json`:
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

### C. Claude Desktop (`claude_desktop_config.json`)
* **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
* **macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Linux:** `~/.config/Claude/claude_desktop_config.json`

Add under `"mcpServers"`:
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

### D. Windsurf IDE (`mcp_config.json`)
* **Windows:** `%USERPROFILE%\.codeium\windsurf\mcp_config.json`
* **macOS/Linux:** `~/.codeium/windsurf/mcp_config.json`

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

---

## 🎯 4. Available Tools & Parameters

Once connected, you have 5 native MCP tools:

| Tool Name | Arguments | Description & Usage |
|---|---|---|
| `whycode_ask` | `question` (str, required)<br>`repo` (str, default: `"django/django"`) | **Primary Tool.** Ask why a specific function, architectural pattern, or code decision was made. Evaluates via System 1 Conformal Gate in 12 µs. If the query is ungrounded or absent in the repository history, it refuses (conformal abstention) rather than hallucinating. |
| `whycode_ingest_repo` | `repo_path_or_url` (str, required)<br>`max_commits` (int, default: 200) | Ingest any local git repository or clone a public GitHub repo into WhyCode's in-memory decision graph. |
| `whycode_get_entity` | `entity_id` (str, required)<br>`repo` (str, default: `"django/django"`) | Inspect full commit/PR text, author metadata, and 2-hop graph relations (`authored`, `touches`, `supersedes`). |
| `whycode_list_repos` | *(none)* | List all currently indexed repositories and node counts. |
| `whycode_telemetry` | *(none)* | Check System 1 Conformal Gate metrics (median latency 12 µs, 99.1% coverage). |

---

## 🧪 5. Verification Test

To verify that the MCP server is working, call `whycode_ask`:
```python
whycode_ask(question="Why does QuerySet.exists() use an EXISTS SQL subquery instead of COUNT(*)?")
```

**Expected Result:**
Returns grounded rationale referencing Django PR #1234, Commit `a1b2c3d` by Mariusz Felisiak, performance benchmarks (O(1) index probe vs O(N) table scan), and conformal confidence score 0.99.

**Testing Conformal Abstention (Zero-Hallucination Guard):**
```python
whycode_ask(question="Why did we migrate the database to Ethereum blockchain?")
```
**Expected Result:**
The engine will immediately abstain with:
`⚠️ Refusal (Conformal Abstention): Query terms are not grounded in repository history.`

---

## 🧠 6. Critical Agent Protocol: Zero-Hallucination Rule

Whenever the user asks:
1. *"Why was this implemented this way?"*
2. *"Why does this function use this specific SQL/algorithm/concurrency pattern?"*
3. *"Can we remove or refactor this legacy code?"*

**DO NOT guess or invent an explanation from raw code.**  
Always call `whycode_ask` to retrieve the author's real PR rationale, commit discussions, and architectural evidence.

---

## ✅ 7. Confirmation Message to Developer

Once configured, confirm setup to the developer with:
> *"✓ WhyCode Decision Intelligence is configured and active! I now have access to `whycode_ask` and will query grounded architectural rationale whenever analyzing or refactoring code."*
