import re

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Remove <div class="badge">...</div> from HTML
badge_pattern = r'<!-- INTEGRATED TELEMETRY BADGE -->\s*<div class="badge">.*?</div>\s*</div>'
html = re.sub(badge_pattern, '', html, flags=re.DOTALL)
print("Removed badge HTML block")

# 2. Add copy handler inside <script>
copy_script = """
    // Hero Agent Pill 1-Click Copy Handler
    const heroCopyBtn = document.getElementById("heroCopyPillBtn");
    const heroCopyPill = document.getElementById("heroAgentPill");
    const heroCopyText = document.getElementById("heroCopyPillText");
    const agentPrompt = "Read whycode/agent.md and configure the WhyCode MCP server in my editor so you can query architectural decisions and PR rationale.";

    function copyHeroPrompt() {
      navigator.clipboard.writeText(agentPrompt).then(() => {
        if (heroCopyBtn) heroCopyBtn.classList.add("copied");
        if (heroCopyText) heroCopyText.textContent = "✓ COPIED!";
        setTimeout(() => {
          if (heroCopyBtn) heroCopyBtn.classList.remove("copied");
          if (heroCopyText) heroCopyText.textContent = "COPY";
        }, 2000);
      }).catch(err => {
        console.warn("Clipboard copy error:", err);
      });
    }

    if (heroCopyBtn) {
      heroCopyBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        copyHeroPrompt();
      });
    }
    if (heroCopyPill) {
      heroCopyPill.addEventListener("click", copyHeroPrompt);
    }
  </script>
</body>"""

html = html.replace('  </script>\n</body>', copy_script)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated index.html with copy handler and removed confidence badge!")
