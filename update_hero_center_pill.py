with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Hide .badge in CSS and style .hero-agent-pill-center
new_css = """
    /* HIDE CONFIDENCE BADGE */
    .badge {
      display: none !important;
    }

    /* CENTERED, LARGER HERO AGENT PILL */
    .hero-agent-pill-center {
      position: relative;
      z-index: 15;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      gap: 12px;
      margin: 40px auto 0;
      width: 100%;
      max-width: 620px;
      text-align: center;
    }
    .hero-agent-pill {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      width: 100%;
      height: 60px;
      padding: 0 10px 0 24px;
      border-radius: 9999px;
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
      border: 1px solid rgba(255, 255, 255, 0.18);
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.25);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
      cursor: pointer;
      user-select: none;
    }
    .hero-agent-pill:hover {
      border-color: rgba(240, 162, 76, 0.6);
      background: linear-gradient(135deg, rgba(255, 255, 255, 0.12) 0%, rgba(255, 255, 255, 0.04) 100%);
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.9), 0 0 30px rgba(240, 162, 76, 0.3);
      transform: translateY(-2px);
    }
    .hero-agent-pill-left {
      display: flex;
      align-items: center;
      gap: 14px;
      overflow: hidden;
      white-space: nowrap;
    }
    .pill-sparkle {
      color: var(--amber);
      font-size: 16px;
      filter: drop-shadow(0 0 8px var(--amber));
    }
    .hero-agent-pill-title {
      font-size: 16px;
      font-weight: 500;
      color: #fff;
      letter-spacing: -0.01em;
    }
    .hero-agent-pill-icons {
      display: flex;
      align-items: center;
      gap: 7px;
      color: rgba(255, 255, 255, 0.45);
      font-size: 15px;
      margin-left: 2px;
    }
    .hero-agent-pill-copy-btn {
      height: 42px;
      padding: 0 18px;
      border-radius: 9999px;
      border: 1px solid rgba(240, 162, 76, 0.45);
      background: linear-gradient(135deg, rgba(240, 162, 76, 0.25) 0%, rgba(240, 162, 76, 0.12) 100%);
      color: #f0a24c;
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 0.05em;
      text-transform: uppercase;
      display: inline-flex;
      align-items: center;
      gap: 7px;
      cursor: pointer;
      flex-shrink: 0;
      transition: all 0.2s ease;
    }
    .hero-agent-pill-copy-btn:hover {
      background: linear-gradient(135deg, rgba(240, 162, 76, 0.45) 0%, rgba(240, 162, 76, 0.22) 100%);
      color: #fff;
      border-color: rgba(240, 162, 76, 0.8);
      box-shadow: 0 0 15px rgba(240, 162, 76, 0.4);
    }
    .hero-agent-pill-copy-btn.copied {
      background: rgba(74, 222, 128, 0.25) !important;
      border-color: rgba(74, 222, 128, 0.6) !important;
      color: #4ade80 !important;
      box-shadow: 0 0 15px rgba(74, 222, 128, 0.4) !important;
    }
    .hero-agent-pill-caption {
      font-size: 13.5px;
      color: var(--body);
      line-height: 1.5;
    }
    .hero-agent-pill-caption code {
      font-family: var(--font-mono);
      font-size: 12px;
      color: #f0a24c;
      background: rgba(240, 162, 76, 0.12);
      border: 1px solid rgba(240, 162, 76, 0.25);
      padding: 2px 6px;
      border-radius: 5px;
    }
"""

# Replace old hero-agent-pill CSS if present, or append
html = html.replace('</style>', new_css + '\n  </style>')

# Remove old hero-agent-pill-wrap from inside hero-right
old_wrap = """        <!-- AGENT-NATIVE ONE-SENTENCE SETUP PILL -->
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
        </div>"""

if old_wrap in html:
    html = html.replace(old_wrap, "")
    print("Removed old hero-agent-pill-wrap from hero-right")

# Insert centered hero-agent-pill-center directly under </div> <!-- hero-grid -->
new_center_pill = """    <!-- CENTERED, LARGER AGENT-NATIVE SETUP PILL -->
    <div class="hero-agent-pill-center">
      <div class="hero-agent-pill" id="heroAgentPill" title="Click to copy prompt for Cursor, Claude Code, or Codex">
        <div class="hero-agent-pill-left">
          <span class="pill-sparkle">✦</span>
          <span class="hero-agent-pill-title">Connect your agent to WhyCode</span>
          <div class="hero-agent-pill-icons">
            <span>✻</span><span>🤖</span><span>◬</span><span>⋀</span>
          </div>
        </div>
        <button type="button" class="hero-agent-pill-copy-btn" id="heroCopyPillBtn">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          <span id="heroCopyPillText">COPY</span>
        </button>
      </div>
      <div class="hero-agent-pill-caption">
        Paste one sentence into Claude Code, Codex, or Cursor. Your agent reads <code>whycode/agent.md</code> and sets it all up.
      </div>
    </div>"""

# Find end of hero-grid
target_grid_end = '    </div>\n\n    <!-- INTEGRATED TELEMETRY BADGE -->'
replacement = '    </div>\n\n' + new_center_pill + '\n\n    <!-- INTEGRATED TELEMETRY BADGE -->'

if target_grid_end in html:
    html = html.replace(target_grid_end, replacement)
    print("Placed hero-agent-pill-center directly after hero-grid!")
else:
    print("Target grid end not found verbatim, searching...")

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated index.html successfully!")
