# -*- coding: utf-8 -*-
with open('template_base.html', 'r', encoding='utf-8') as f:
    html = f.read()

badge_block = """        <div class="composer-repo-badge" style="display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-family: 'Geist Mono', monospace; color: var(--muted); user-select: none;">
          <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 8px var(--accent);"></span>
          <span>django/django · 678 nodes</span>
        </div>"""

if badge_block in html:
    html = html.replace(badge_block, "        <div></div>")
    print("Removed repo badge cleanly!")
else:
    print("Could not find exact badge block")

with open('template_base.html', 'w', encoding='utf-8') as f:
    f.write(html)
