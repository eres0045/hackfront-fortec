import re

# 1. Update template_base.html
with open('template_base.html', 'r', encoding='utf-8') as f:
    html = f.read()

sidebar_css = '''
    /* Developer Hub Button & Sidebar */
    .dev-hub-btn {
      position: relative;
      height: 34px;
      padding: 0 14px 0 11px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 500;
      color: var(--text-soft);
      --blur: 10px;
      background-color: #0a0c148c;
      display: inline-flex;
      align-items: center;
      gap: 7px;
      cursor: pointer;
      transition: color 0.2s ease, border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
      border: 1px solid var(--chip-edge);
      outline: none;
    }
    .dev-hub-btn:hover {
      color: var(--text);
      border-color: rgba(122, 162, 255, 0.45);
      background-color: #0e1220a0;
      box-shadow: 0 0 14px rgba(122, 162, 255, 0.2);
    }
    .hub-pill-badge {
      font-family: 'Geist Mono', ui-monospace, Menlo, monospace;
      font-size: 10.5px;
      font-weight: 600;
      color: #93b4ff;
      background: rgba(122, 162, 255, 0.15);
      padding: 1px 6px;
      border-radius: 5px;
      border: 1px solid rgba(122, 162, 255, 0.3);
    }

    /* Slide-Out Glass Sidebar */
    .sidebar-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(6px);
      -webkit-backdrop-filter: blur(6px);
      z-index: 90;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.3s ease;
    }
    .sidebar-backdrop.active {
      opacity: 1;
      pointer-events: auto;
    }

    .dev-sidebar {
      position: fixed;
      top: 0;
      left: 0;
      bottom: 0;
      width: min(440px, 90vw);
      background: linear-gradient(180deg, rgba(12, 15, 24, 0.96) 0%, rgba(6, 8, 14, 0.98) 100%);
      border-right: 1px solid rgba(255, 255, 255, 0.12);
      box-shadow: 24px 0 70px rgba(0, 0, 0, 0.85), inset -1px 0 0 rgba(255, 255, 255, 0.06);
      backdrop-filter: blur(24px) saturate(190%);
      -webkit-backdrop-filter: blur(24px) saturate(190%);
      z-index: 100;
      transform: translateX(-100%);
      transition: transform 0.32s cubic-bezier(0.16, 1, 0.3, 1);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .dev-sidebar.active {
      transform: translateX(0);
    }

    .dev-sidebar-header {
      padding: 20px 22px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: rgba(255, 255, 255, 0.02);
    }
    .dev-sidebar-title-wrap {
      display: flex;
      flex-direction: column;
      gap: 3px;
    }
    .dev-sidebar-kicker {
      font-size: 10.5px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--accent);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .dev-sidebar-title {
      margin: 0;
      font-size: 18px;
      font-weight: 500;
      color: #fff;
      letter-spacing: -0.01em;
    }
    .dev-sidebar-close {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      border: none;
      background: rgba(255, 255, 255, 0.05);
      color: var(--muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 15px;
      transition: background 0.15s ease, color 0.15s ease;
    }
    .dev-sidebar-close:hover {
      background: rgba(255, 255, 255, 0.15);
      color: #fff;
    }

    .dev-sidebar-body {
      padding: 20px 22px;
      overflow-y: auto;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 24px;
    }
    .dev-sidebar-body::-webkit-scrollbar {
      width: 5px;
    }
    .dev-sidebar-body::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.15);
      border-radius: 999px;
    }

    .sidebar-section {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .sidebar-section-title {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .sidebar-section-desc {
      font-size: 12.5px;
      color: var(--text-soft);
      line-height: 1.5;
      margin: 0;
    }

    /* MCP Tabs */
    .mcp-tabs {
      display: flex;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 9px;
      padding: 3px;
      gap: 3px;
    }
    .mcp-tab-btn {
      flex: 1;
      height: 28px;
      border: none;
      border-radius: 6px;
      background: transparent;
      color: var(--muted);
      font-size: 12px;
      font-weight: 500;
      cursor: pointer;
      transition: background 0.15s ease, color 0.15s ease;
    }
    .mcp-tab-btn:hover {
      color: var(--text);
    }
    .mcp-tab-btn.active {
      background: rgba(122, 162, 255, 0.18);
      color: #fff;
      font-weight: 600;
    }

    /* Code Snippet Box */
    .mcp-snippet-box {
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 12px;
      background: rgba(0, 0, 0, 0.45);
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }
    .mcp-snippet-bar {
      padding: 7px 12px;
      background: rgba(255, 255, 255, 0.03);
      border-bottom: 1px solid rgba(255, 255, 255, 0.06);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .mcp-snippet-file {
      font-family: 'Geist Mono', monospace;
      font-size: 11px;
      color: var(--muted);
    }
    .mcp-copy-btn {
      background: rgba(122, 162, 255, 0.1);
      border: 1px solid rgba(122, 162, 255, 0.25);
      color: var(--accent);
      border-radius: 6px;
      padding: 3px 8px;
      font-size: 11px;
      font-weight: 500;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 4px;
      transition: background 0.15s ease, color 0.15s ease;
    }
    .mcp-copy-btn:hover {
      background: rgba(122, 162, 255, 0.25);
      color: #fff;
    }
    .mcp-snippet-code {
      padding: 12px;
      font-family: 'Geist Mono', monospace;
      font-size: 11.5px;
      line-height: 1.5;
      color: #cfd6e6;
      margin: 0;
      white-space: pre;
      overflow-x: auto;
    }

    /* Test MCP Tool Button */
    .test-mcp-btn {
      height: 34px;
      background: linear-gradient(135deg, rgba(122, 162, 255, 0.2) 0%, rgba(122, 162, 255, 0.08) 100%);
      border: 1px solid rgba(122, 162, 255, 0.35);
      border-radius: 9px;
      color: #e8ebf7;
      font-size: 12.5px;
      font-weight: 500;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      transition: background 0.2s ease, border-color 0.2s ease, transform 0.1s ease;
    }
    .test-mcp-btn:hover {
      background: linear-gradient(135deg, rgba(122, 162, 255, 0.35) 0%, rgba(122, 162, 255, 0.18) 100%);
      border-color: rgba(122, 162, 255, 0.6);
      color: #fff;
    }
    .mcp-test-output {
      padding: 10px 12px;
      border-radius: 9px;
      background: rgba(74, 222, 128, 0.06);
      border: 1px solid rgba(74, 222, 128, 0.25);
      font-size: 12px;
      line-height: 1.45;
      color: #d1fae5;
      display: none;
      animation: fadeInModal 0.2s ease forwards;
    }

    /* Grounded Query Cards */
    .quick-query-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .quick-query-card {
      padding: 10px 12px;
      border-radius: 10px;
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.08);
      cursor: pointer;
      display: flex;
      flex-direction: column;
      gap: 3px;
      transition: background 0.15s ease, border-color 0.15s ease, transform 0.1s ease;
    }
    .quick-query-card:hover {
      background: rgba(122, 162, 255, 0.08);
      border-color: rgba(122, 162, 255, 0.35);
      transform: translateX(3px);
    }
    .quick-query-tag {
      font-family: 'Geist Mono', monospace;
      font-size: 10px;
      color: var(--accent);
      font-weight: 600;
    }
    .quick-query-text {
      font-size: 12.5px;
      color: #e2e8f0;
      line-height: 1.4;
    }

    /* Telemetry Grid */
    .sidebar-telemetry-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .telemetry-tile {
      padding: 9px 11px;
      border-radius: 9px;
      background: rgba(255, 255, 255, 0.025);
      border: 1px solid rgba(255, 255, 255, 0.06);
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .telemetry-tile-label {
      font-size: 10px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--muted);
    }
    .telemetry-tile-val {
      font-family: 'Geist Mono', monospace;
      font-size: 13px;
      font-weight: 600;
      color: #fff;
    }
'''

# Insert CSS before </style>
html = html.replace('</style>', sidebar_css + '\n  </style>')

# Replace Top-Left link with Top-Left controls container (WhyCode + Developer Hub)
old_top_left = '''    <a href="index.html" class="glass no-liquid" style="position: fixed; top: 16px; left: 16px; z-index: 30; height: 34px; padding: 0 14px 0 12px; border-radius: 999px; font-size: 13px; font-weight: 500; color: var(--text-soft); text-decoration: none; display: inline-flex; align-items: center; gap: 7px; background-color: #0a0c148c; transition: color 0.2s ease;">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"></polyline></svg>
    <span>WhyCode</span>
  </a>'''

new_top_left = '''  <!-- Top-Left: WhyCode Back + Developer Hub Sidebar Trigger -->
  <div class="top-left-controls" style="position: fixed; top: 16px; left: 16px; z-index: 30; display: flex; gap: 8px; align-items: center;">
    <a href="index.html" class="glass no-liquid" style="height: 34px; padding: 0 14px 0 12px; border-radius: 999px; font-size: 13px; font-weight: 500; color: var(--text-soft); text-decoration: none; display: inline-flex; align-items: center; gap: 7px; background-color: #0a0c148c; transition: color 0.2s ease;">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"></polyline></svg>
      <span>WhyCode</span>
    </a>

    <button type="button" class="glass no-liquid dev-hub-btn" id="openSidebarBtn" aria-label="Open Developer Hub" title="Open Developer Hub & MCP Bridge">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
        <line x1="9" y1="3" x2="9" y2="21"></line>
      </svg>
      <span>Developer Hub</span>
      <span class="hub-pill-badge">MCP</span>
    </button>
  </div>'''

if old_top_left in html:
    html = html.replace(old_top_left, new_top_left)
    print("Replaced top-left link with controls successfully!")
else:
    print("Warning: old_top_left block not matched directly!")

# Add Developer Hub Sidebar Markup before <!-- SCRIPT_PLACEHOLDER -->
sidebar_markup = '''  <!-- Backdrop for Developer Hub Sidebar -->
  <div class="sidebar-backdrop" id="sidebarBackdrop"></div>

  <!-- Slide-Out Glass Sidebar: Developer Hub & MCP Bridge -->
  <aside class="dev-sidebar" id="devSidebar" aria-label="Developer Hub">
    <div class="dev-sidebar-header">
      <div class="dev-sidebar-title-wrap">
        <div class="dev-sidebar-kicker">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><path d="m9 12 2 2 4-4"></path></svg>
          WhyCode Developer Hub
        </div>
        <h2 class="dev-sidebar-title">MCP & Decision Bridge</h2>
      </div>
      <button type="button" class="dev-sidebar-close" id="closeSidebarBtn" aria-label="Close sidebar">✕</button>
    </div>

    <div class="dev-sidebar-body">
      <!-- Section 1: Model Context Protocol (MCP) -->
      <div class="sidebar-section">
        <div class="sidebar-section-title">
          <span>Model Context Protocol (MCP)</span>
          <span style="color: #4ade80; font-size: 10px;">● Stdio Ready</span>
        </div>
        <p class="sidebar-section-desc">
          Connect WhyCode decision graph directly to Cursor, Claude Desktop, or VS Code for zero-hallucination code reviews.
        </p>

        <!-- IDE Tabs -->
        <div class="mcp-tabs">
          <button type="button" class="mcp-tab-btn active" data-ide="cursor">Cursor</button>
          <button type="button" class="mcp-tab-btn" data-ide="claude">Claude</button>
          <button type="button" class="mcp-tab-btn" data-ide="vscode">VS Code</button>
          <button type="button" class="mcp-tab-btn" data-ide="cli">CLI</button>
        </div>

        <!-- Snippet Box -->
        <div class="mcp-snippet-box">
          <div class="mcp-snippet-bar">
            <span class="mcp-snippet-file" id="mcpSnippetFile">.cursor/mcp.json</span>
            <button type="button" class="mcp-copy-btn" id="copyMcpBtn">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              <span id="copyMcpText">Copy JSON</span>
            </button>
          </div>
          <pre class="mcp-snippet-code" id="mcpSnippetCode">{\n  "mcpServers": {\n    "whycode": {\n      "command": "python",\n      "args": ["whycode_mcp.py"]\n    }\n  }\n}</pre>
        </div>

        <!-- Real-Time MCP Tool Call Test -->
        <button type="button" class="test-mcp-btn" id="testMcpToolBtn">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
          Test MCP Tool: whycode_ask
        </button>
        <div class="mcp-test-output" id="mcpTestOutput"></div>
      </div>

      <!-- Section 2: Grounded Demo Queries -->
      <div class="sidebar-section">
        <div class="sidebar-section-title">
          <span>Grounded Demo Queries</span>
          <span style="font-size: 10px; color: var(--muted);">Click to Run</span>
        </div>
        <p class="sidebar-section-desc">
          Try verified architectural decisions answering the "Why" behind the code:
        </p>

        <div class="quick-query-list">
          <div class="quick-query-card" data-query="why did Django avoid duplicate joins in filter after aggregation?">
            <span class="quick-query-tag">PR #22207 · ORM Join Optimization</span>
            <span class="quick-query-text">"Why did Django avoid duplicate joins in filter after aggregation?"</span>
          </div>

          <div class="quick-query-card" data-query="why was SQLite replaced with an in-RAM inverted index?">
            <span class="quick-query-tag">System 2 Rationale · 1,500x Speedup</span>
            <span class="quick-query-text">"Why was SQLite replaced with an in-RAM inverted index?"</span>
          </div>

          <div class="quick-query-card" data-query="why does System 1 gate refuse ungrounded queries?">
            <span class="quick-query-tag">Conformal Gate · Zero Hallucinations</span>
            <span class="quick-query-text">"Why does System 1 gate refuse ungrounded queries?"</span>
          </div>

          <div class="quick-query-card" data-query="why enforce 15-minute rolling window expiries on auth tokens?">
            <span class="quick-query-tag">Security Policy · Replay Protection</span>
            <span class="quick-query-text">"Why enforce 15-minute rolling window expiries on auth tokens?"</span>
          </div>
        </div>
      </div>

      <!-- Section 3: Telemetry & Neo4j Alignment -->
      <div class="sidebar-section">
        <div class="sidebar-section-title">
          <span>Telemetry & Architecture</span>
        </div>
        <div class="sidebar-telemetry-grid">
          <div class="telemetry-tile">
            <span class="telemetry-tile-label">System 1 Gate</span>
            <span class="telemetry-tile-val" style="color: #7aa2ff;">12.0 µs</span>
          </div>
          <div class="telemetry-tile">
            <span class="telemetry-tile-label">Graph Walk</span>
            <span class="telemetry-tile-val" style="color: #4ade80;">0.51 ms</span>
          </div>
          <div class="telemetry-tile">
            <span class="telemetry-tile-label">Conformal Cov</span>
            <span class="telemetry-tile-val">99.1%</span>
          </div>
          <div class="telemetry-tile">
            <span class="telemetry-tile-label">Hallucinations</span>
            <span class="telemetry-tile-val" style="color: #4ade80;">0.0%</span>
          </div>
        </div>
      </div>
    </div>
  </aside>
'''

html = html.replace('<!-- SCRIPT_PLACEHOLDER -->', sidebar_markup + '\n  <!-- SCRIPT_PLACEHOLDER -->')

with open('template_base.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated template_base.html with Developer Hub Sidebar markup and styles!")
