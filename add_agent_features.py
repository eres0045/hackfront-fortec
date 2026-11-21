import re
import json

AGENT_PROMPT = "Read whycode/agent.md and configure the WhyCode MCP server in my editor so you can query architectural decisions and PR rationale."

# ==============================================================================
# 1. Update template_base.html (Query Area Sidebar)
# ==============================================================================
with open('template_base.html', 'r', encoding='utf-8') as f:
    tpl = f.read()

agent_pill_sidebar_css = """
    /* Agent-Native Setup Pill */
    .agent-pill-container {
      display: flex;
      flex-direction: column;
      gap: 7px;
      margin: 4px 0 14px;
      width: 100%;
    }
    .agent-pill {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      width: 100%;
      height: 44px;
      padding: 0 6px 0 14px;
      border-radius: 999px;
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.03) 100%);
      border: 1px solid rgba(255, 255, 255, 0.16);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.18);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      transition: border-color 0.25s ease, box-shadow 0.25s ease, background 0.25s ease;
      cursor: pointer;
      user-select: none;
    }
    .agent-pill:hover {
      border-color: rgba(122, 162, 255, 0.55);
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.05) 100%);
      box-shadow: 0 12px 30px rgba(0, 0, 0, 0.65), 0 0 20px rgba(122, 162, 255, 0.25);
    }
    .agent-pill-left {
      display: flex;
      align-items: center;
      gap: 8px;
      overflow: hidden;
      white-space: nowrap;
    }
    .agent-pill-title {
      font-size: 13px;
      font-weight: 500;
      color: #fff;
      letter-spacing: -0.01em;
    }
    .agent-pill-icons {
      display: flex;
      align-items: center;
      gap: 4px;
      color: var(--muted);
      font-size: 11px;
    }
    .agent-pill-copy-btn {
      height: 30px;
      padding: 0 11px;
      border-radius: 999px;
      border: 1px solid rgba(122, 162, 255, 0.35);
      background: rgba(122, 162, 255, 0.15);
      color: #93b4ff;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      cursor: pointer;
      flex-shrink: 0;
      transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
    }
    .agent-pill-copy-btn:hover {
      background: rgba(122, 162, 255, 0.3);
      color: #fff;
      border-color: rgba(122, 162, 255, 0.6);
    }
    .agent-pill-copy-btn.copied {
      background: rgba(74, 222, 128, 0.2) !important;
      border-color: rgba(74, 222, 128, 0.5) !important;
      color: #4ade80 !important;
    }
    .agent-pill-caption {
      font-size: 11.5px;
      color: var(--text-soft);
      line-height: 1.4;
      margin: 0;
    }
    .agent-pill-caption code {
      font-family: 'Geist Mono', monospace;
      font-size: 10.5px;
      color: #93b4ff;
      background: rgba(122, 162, 255, 0.1);
      padding: 1px 4px;
      border-radius: 4px;
    }
"""

if '.agent-pill-container' not in tpl:
    tpl = tpl.replace('</style>', agent_pill_sidebar_css + '\n  </style>')

sidebar_pill_html = """        <!-- Agent-Native 1-Click Setup Pill -->
        <div class="agent-pill-container">
          <div class="agent-pill" id="sidebarAgentPill" title="Click to copy prompt for Cursor, Claude Code, or Codex">
            <div class="agent-pill-left">
              <span style="color: var(--accent);">✦</span>
              <span class="agent-pill-title">Connect your agent to WhyCode</span>
              <div class="agent-pill-icons">
                <span>✻</span><span>🤖</span><span>◬</span><span>⋀</span>
              </div>
            </div>
            <button type="button" class="agent-pill-copy-btn" id="sidebarCopyPillBtn">
              <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              <span id="sidebarCopyPillText">COPY</span>
            </button>
          </div>
          <p class="agent-pill-caption">
            Paste one sentence into Cursor, Claude Code, or Codex. Your agent reads <code>whycode/agent.md</code> and sets it all up.
          </p>
        </div>
"""

old_sidebar_section = '<div class="sidebar-section">\n        <div class="sidebar-section-title">\n          <span>Model Context Protocol (MCP)</span>'
new_sidebar_section = f'<div class="sidebar-section">\n        <div class="sidebar-section-title">\n          <span>Model Context Protocol (MCP)</span>'

if sidebar_pill_html not in tpl:
    tpl = tpl.replace('<p class="sidebar-section-desc">\n          Connect WhyCode decision graph directly to Cursor, Claude Desktop, or VS Code for zero-hallucination code reviews.\n        </p>', 
                      '<p class="sidebar-section-desc">\n          Connect WhyCode decision graph directly to Cursor, Claude Desktop, or VS Code for zero-hallucination code reviews.\n        </p>\n' + sidebar_pill_html)
    print("Added agent pill to template_base.html sidebar!")

with open('template_base.html', 'w', encoding='utf-8') as f:
    f.write(tpl)


# ==============================================================================
# 2. Update glyph_animals_engine.js (Query Area JS logic)
# ==============================================================================
with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    js = f.read()

agent_pill_js = f'''
  // --- Agent-Native Pill 1-Click Copy ---
  const sidebarAgentPill = document.getElementById('sidebarAgentPill');
  const sidebarCopyPillBtn = document.getElementById('sidebarCopyPillBtn');
  const sidebarCopyPillText = document.getElementById('sidebarCopyPillText');
  const agentPromptText = {json.dumps(AGENT_PROMPT)};

  function copyAgentPrompt() {{
    navigator.clipboard.writeText(agentPromptText).then(() => {{
      if (sidebarCopyPillBtn) sidebarCopyPillBtn.classList.add('copied');
      if (sidebarCopyPillText) sidebarCopyPillText.textContent = '✓ COPIED!';
      setTimeout(() => {{
        if (sidebarCopyPillBtn) sidebarCopyPillBtn.classList.remove('copied');
        if (sidebarCopyPillText) sidebarCopyPillText.textContent = 'COPY';
      }}, 2000);
    }}).catch(err => {{
      console.warn('Clipboard write failed:', err);
    }});
  }}

  if (sidebarCopyPillBtn) sidebarCopyPillBtn.addEventListener('click', (e) => {{
    e.stopPropagation();
    copyAgentPrompt();
  }});
  if (sidebarAgentPill) sidebarAgentPill.addEventListener('click', copyAgentPrompt);
'''

if 'sidebarCopyPillBtn' not in js:
    js += '\n' + agent_pill_js
    with open('glyph_animals_engine.js', 'w', encoding='utf-8') as f:
        f.write(js)
    print("Added agent pill copy logic to glyph_animals_engine.js!")


# ==============================================================================
# 3. Update index.html (Landing Page Hero + #mcp Section + Copy logic)
# ==============================================================================
with open('index.html', 'r', encoding='utf-8') as f:
    idx = f.read()

# Add CSS for Landing Page Agent Pill & #mcp section
index_pill_css = """
    /* HERO AGENT-NATIVE SETUP PILL */
    .hero-agent-pill-wrap {
      display: flex;
      flex-direction: column;
      gap: 10px;
      margin-top: 24px;
      width: 100%;
      max-width: 520px;
    }
    .hero-agent-pill {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      width: 100%;
      height: 52px;
      padding: 0 8px 0 18px;
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.15);
      box-shadow: 0 14px 40px rgba(0, 0, 0, 0.7), inset 0 1px 0 rgba(255, 255, 255, 0.2);
      backdrop-filter: blur(14px);
      -webkit-backdrop-filter: blur(14px);
      transition: all 0.25s ease;
      cursor: pointer;
      user-select: none;
    }
    .hero-agent-pill:hover {
      border-color: rgba(240, 162, 76, 0.5);
      background: rgba(255, 255, 255, 0.08);
      box-shadow: 0 16px 45px rgba(0, 0, 0, 0.8), 0 0 25px rgba(240, 162, 76, 0.25);
    }
    .hero-agent-pill-left {
      display: flex;
      align-items: center;
      gap: 10px;
      overflow: hidden;
      white-space: nowrap;
    }
    .hero-agent-pill-title {
      font-size: 14px;
      font-weight: 500;
      color: #fff;
      letter-spacing: -0.01em;
    }
    .hero-agent-pill-icons {
      display: flex;
      align-items: center;
      gap: 5px;
      color: var(--muted);
      font-size: 12.5px;
    }
    .hero-agent-pill-copy-btn {
      height: 36px;
      padding: 0 14px;
      border-radius: 999px;
      border: 1px solid rgba(240, 162, 76, 0.4);
      background: rgba(240, 162, 76, 0.15);
      color: #f0a24c;
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      flex-shrink: 0;
      transition: all 0.2s ease;
    }
    .hero-agent-pill-copy-btn:hover {
      background: rgba(240, 162, 76, 0.3);
      color: #fff;
      border-color: rgba(240, 162, 76, 0.7);
    }
    .hero-agent-pill-copy-btn.copied {
      background: rgba(74, 222, 128, 0.2) !important;
      border-color: rgba(74, 222, 128, 0.5) !important;
      color: #4ade80 !important;
    }
    .hero-agent-pill-caption {
      font-size: 13px;
      color: var(--body);
      line-height: 1.5;
    }
    .hero-agent-pill-caption code {
      font-family: var(--font-mono);
      font-size: 11.5px;
      color: #f0a24c;
      background: rgba(240, 162, 76, 0.1);
      padding: 1px 5px;
      border-radius: 4px;
    }

    /* SECTION MCP */
    .section-mcp {
      padding: 80px 4vw;
      border-top: 1px solid var(--border);
      background: radial-gradient(circle at 50% 0%, rgba(122, 162, 255, 0.07) 0%, transparent 70%);
    }
    .mcp-container {
      max-width: 1100px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 32px;
    }
"""

if '.hero-agent-pill-wrap' not in idx:
    idx = idx.replace('</style>', index_pill_css + '\n  </style>')

# Add nav link for MCP Server
if '<a href="#mcp" class="nav-link">MCP Server</a>' not in idx:
    idx = idx.replace('<a href="#byo" class="nav-link">BYO Repo</a>', '<a href="#byo" class="nav-link">BYO Repo</a>\n      <a href="#mcp" class="nav-link">MCP Server</a>')

# Add Hero Agent Pill
hero_pill_html = """
        <!-- AGENT-NATIVE ONE-SENTENCE SETUP PILL -->
        <div class="hero-agent-pill-wrap">
          <div class="hero-agent-pill" id="heroAgentPill" title="Click to copy prompt for Cursor, Claude Code, or Codex">
            <div class="hero-agent-pill-left">
              <span style="color: var(--amber);">✦</span>
              <span class="hero-agent-pill-title">Connect your agent to WhyCode</span>
              <div class="hero-agent-pill-icons">
                <span>✻</span><span>🤖</span><span>◬</span><span>⋀</span>
              </div>
            </div>
            <button type="button" class="hero-agent-pill-copy-btn" id="heroCopyPillBtn">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
              <span id="heroCopyPillText">COPY</span>
            </button>
          </div>
          <div class="hero-agent-pill-caption">
            Paste one sentence into Claude Code, Codex, or Cursor. Your agent reads <code>whycode/agent.md</code> and sets it all up.
          </div>
        </div>
"""

if 'heroAgentPill' not in idx:
    old_ctas = """        <div class="hero-ctas">
          <a href="glyph_animals.html" class="btn-amber-glass">
            <span>Ask a Decision</span>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </a>
          <a href="#byo" class="btn-github">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
            <span>Ingest Your Repo</span>
          </a>
        </div>"""
    idx = idx.replace(old_ctas, old_ctas + hero_pill_html)
    print("Added hero agent pill to index.html!")

# Add #mcp section right after #byo
mcp_section_html = """
  <!-- 3.5 MODEL CONTEXT PROTOCOL (MCP) & IDE BRIDGE -->
  <section class="section-mcp" id="mcp">
    <div class="mcp-container">
      <div style="text-align: center; max-width: 720px; margin: 0 auto;">
        <div class="studio-kicker" style="justify-content: center;">
          <span>✦ Model Context Protocol (MCP) · Stdio JSON-RPC 2.0</span>
        </div>
        <h2 style="font-family: var(--font-serif); font-size: 38px; letter-spacing: -0.02em; margin-bottom: 12px;">Put architectural decision intelligence inside your IDE.</h2>
        <p style="color: var(--body); font-size: 15.5px; line-height: 1.6;">
          WhyCode exposes an official MCP server. When an AI agent modifies complex code in Cursor, Claude Desktop, or VS Code, it queries WhyCode to understand past design rationale with 12 µs non-autoregressive verification.
        </p>
      </div>

      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px;">
        <div style="padding: 24px; border-radius: 16px; background: rgba(255,255,255,0.03); border: 1px solid var(--border); display: flex; flex-direction: column; gap: 12px;">
          <div style="font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; color: var(--amber); font-weight: 600;">1. Zero-Friction Agent Prompt</div>
          <h4 style="font-size: 18px; margin: 0; color: #fff;">Just ask your agent</h4>
          <p style="color: var(--body); font-size: 13.5px; line-height: 1.5; margin: 0;">
            Copy one sentence into Cursor, Claude Code, or Codex. Your agent reads <code>whycode/agent.md</code> and registers the tools automatically.
          </p>
          <div style="padding: 12px; border-radius: 8px; background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.08); font-family: var(--font-mono); font-size: 12px; color: #f0a24c;">
            "Read whycode/agent.md and configure the WhyCode MCP server in my editor."
          </div>
        </div>

        <div style="padding: 24px; border-radius: 16px; background: rgba(255,255,255,0.03); border: 1px solid var(--border); display: flex; flex-direction: column; gap: 12px;">
          <div style="font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; color: var(--green); font-weight: 600;">2. Pre-Configured in Repository</div>
          <h4 style="font-size: 18px; margin: 0; color: #fff;">Out of the box in Cursor</h4>
          <p style="color: var(--body); font-size: 13.5px; line-height: 1.5; margin: 0;">
            <code>.cursor/mcp.json</code> and <code>whycode_mcp.py</code> are included in the repo. Opening this project in Cursor enables <code>whycode_ask</code> instantly.
          </p>
          <div style="padding: 12px; border-radius: 8px; background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.08); font-family: var(--font-mono); font-size: 12px; color: #4ade80;">
            ✓ Registered: whycode_ask, whycode_ingest_repo, whycode_get_entity
          </div>
        </div>

        <div style="padding: 24px; border-radius: 16px; background: rgba(255,255,255,0.03); border: 1px solid var(--border); display: flex; flex-direction: column; gap: 12px;">
          <div style="font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; color: #7aa2ff; font-weight: 600;">3. Anti-Hallucination Conformal Gate</div>
          <h4 style="font-size: 18px; margin: 0; color: #fff;">Strict Refusal Guarantee</h4>
          <p style="color: var(--body); font-size: 13.5px; line-height: 1.5; margin: 0;">
            If an agent queries an ungrounded term or empty evidence chain, System 1 refuses with 0.99 confidence, preventing LLM fabrication.
          </p>
          <div style="padding: 12px; border-radius: 8px; background: rgba(0,0,0,0.5); border: 1px solid rgba(255,255,255,0.08); font-family: var(--font-mono); font-size: 12px; color: #7aa2ff;">
            12.0 µs Latency · 0.0% Hallucination Rate
          </div>
        </div>
      </div>
    </div>
  </section>
"""

if 'id="mcp"' not in idx:
    idx = idx.replace('</section>\n\n  <!-- 4. DUAL-PROCESS SPECS', '</section>\n' + mcp_section_html + '\n  <!-- 4. DUAL-PROCESS SPECS')
    print("Added #mcp section to index.html!")

# Add JS copy listener for heroCopyPillBtn
hero_copy_js = f"""
    // Hero Agent Pill Copy Handler
    const heroCopyBtn = document.getElementById('heroCopyPillBtn');
    const heroCopyPill = document.getElementById('heroAgentPill');
    const heroCopyText = document.getElementById('heroCopyPillText');
    const promptText = {json.dumps(AGENT_PROMPT)};

    function copyHeroPrompt() {{
      navigator.clipboard.writeText(promptText).then(() => {{
        if (heroCopyBtn) heroCopyBtn.classList.add('copied');
        if (heroCopyText) heroCopyText.textContent = '✓ COPIED!';
        setTimeout(() => {{
          if (heroCopyBtn) heroCopyBtn.classList.remove('copied');
          if (heroCopyText) heroCopyText.textContent = 'COPY';
        }}, 2000);
      }}).catch(err => console.warn('Copy failed:', err));
    }}

    if (heroCopyBtn) heroCopyBtn.addEventListener('click', (e) => {{ e.stopPropagation(); copyHeroPrompt(); }});
    if (heroCopyPill) heroCopyPill.addEventListener('click', copyHeroPrompt);
"""

if 'heroCopyPillBtn' not in idx:
    idx = idx.replace('</script>\n</body>', hero_copy_js + '\n</script>\n</body>')

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(idx)
print("Updated index.html successfully!")
