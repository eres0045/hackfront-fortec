# WhyCode — Decision Intelligence (hackFront India 2026 Grand Finale)

**Team FORTEC:** Ronit Shrimankar (Lead), Udita Singh (Team Lead)  
**Theme:** T-1: AI & Developer Tools  
**Track:** T1.1 *"Why The Code Is Like This"* (Neo4j Partner Alignment)  
**Venue:** IIIT Delhi — National Grand Finale (21–22 November 2026)

---

## 🎯 What is WhyCode?

Traditional code intelligence answers **what** the code does and **who** wrote it (`git blame`).  
**WhyCode answers *WHY* the code was written this way.**

WhyCode ingests commit history, PR review discussions, issue tickets (Trac/GitHub), and design proposals (DEPs/RFCs) into an in-memory knowledge graph. When a developer or AI agent asks a question:
1. **System 1 (Conformal Gate, 12 µs):** Non-autoregressively screens the query. If a term is ungrounded or absent in the repository, WhyCode **strictly refuses to hallucinate** with 0.99 conformal confidence.
2. **System 2 (Graph Traversal, 0.51 ms):** Walks multi-hop evidence chains, detects superseded decisions, and cites exact author rationale and commit links.

---

## 🔌 Model Context Protocol (MCP) Server for Agents & IDEs

WhyCode includes a native **Model Context Protocol (MCP)** server so any AI agent or IDE (**Cursor, Claude Desktop, Antigravity, VS Code, Windsurf**) can query repository decision rationale directly.

### Tools Exposed to AI Agents:
* `whycode_ask(question, repo)`: Ask any architectural "why" question. Returns grounded author rationale, PR/DEP links, and confidence, or refuses cleanly.
* `whycode_ingest_repo(repo_path_or_url, max_commits)`: Ingest any public GitHub repository on the fly into the decision graph.
* `whycode_get_entity(entity_id, repo)`: Inspect full PR/commit bodies and 2-hop graph relations (authored, touches, supersedes).
* `whycode_list_repos()`: List all connected repositories and node counts.
* `whycode_telemetry()`: Real-time telemetry (12 µs System 1 latency, 99.1% conformal coverage).

---

## 🚀 Setup & IDE Integration

### 1. Cursor IDE Setup
Add to `.cursor/mcp.json` or your Cursor settings:
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

### 2. Claude Desktop Setup
Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "whycode": {
      "command": "python",
      "args": ["C:/absolute/path/to/hackfront-fortec-main/whycode_mcp.py"]
    }
  }
}
```

### 3. CLI Direct Query
```bash
python -m whycode.cli --db data/whycode.db --question "Why did Django avoid duplicate joins in filter after aggregation?"
```

### 4. Zero-Dependency Query Area (Web UI)
Open `glyph_animals.html` or `query.html` in any browser:
* **Single-Line Glass Capsule**: Sleek floating glass search bar with real-time Speech-to-Text microphone.
* **Connect Repo Modal**: Ingest any GitHub repository or pick from one-click presets (`django`, `requests`, `flask`, `fastapi`).
* **Procedural 2D ASCII Canvas**: 60 FPS ASCII simulation with animal visibility toggle.

---

## 🧪 Verification & Unit Tests

Run the full test suite (including System 1 Conformal Gate & MCP tools):
```bash
python -m unittest discover tests
```
*All 24 unit and integration tests execute in ~0.11s with 100% pass rate.*
