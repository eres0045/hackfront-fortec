# -*- coding: utf-8 -*-
"""
Removes 'click to scatter' and the 'Tweaks' button/panel.
Preserves the 'Animals ON/OFF' toggle button at top-right.
"""

# 1. Update template_base.html
with open('template_base.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Remove <p class="hint">click to scatter</p>
if '<p class="hint">click to scatter</p>' in html:
    html = html.replace('<p class="hint">click to scatter</p>', '')
    print("Removed <p class='hint'>click to scatter</p>")

# Replace top-right-controls to only contain toggleAnimalsBtn
old_controls_block = """  <div class="top-right-controls" style="position: fixed; top: 16px; right: 16px; z-index: 30; display: flex; gap: 8px; align-items: center;">
    <button type="button" class="toggle-animals-btn glass no-liquid" id="toggleAnimalsBtn" aria-label="Toggle animals appearance">
      <span class="animal-toggle-dot" id="animalToggleDot" style="width: 7px; height: 7px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 8px #4ade80; transition: background 0.2s ease, box-shadow 0.2s ease;"></span>
      <span id="toggleAnimalsText">Animals ON</span>
    </button>
    <button type="button" class="tweaks-opener glass no-liquid" id="tweaksOpener" aria-label="Open tweaks" style="position: static; top: auto; right: auto;">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="4" y1="21" x2="4" y2="14"></line>
        <line x1="4" y1="10" x2="4" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="12"></line>
        <line x1="12" y1="8" x2="12" y2="3"></line>
        <line x1="20" y1="21" x2="20" y2="16"></line>
        <line x1="20" y1="12" x2="20" y2="3"></line>
        <line x1="1" y1="14" x2="7" y2="14"></line>
        <line x1="9" y1="8" x2="15" y2="8"></line>
        <line x1="17" y1="16" x2="23" y2="16"></line>
      </svg>
      <span>Tweaks</span>
    </button>
  </div>"""

new_controls_block = """  <div class="top-right-controls" style="position: fixed; top: 16px; right: 16px; z-index: 30; display: flex; gap: 8px; align-items: center;">
    <button type="button" class="toggle-animals-btn glass no-liquid" id="toggleAnimalsBtn" aria-label="Toggle animals appearance">
      <span class="animal-toggle-dot" id="animalToggleDot" style="width: 7px; height: 7px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 8px #4ade80; transition: background 0.2s ease, box-shadow 0.2s ease;"></span>
      <span id="toggleAnimalsText">Animals ON</span>
    </button>
  </div>"""

if old_controls_block in html:
    html = html.replace(old_controls_block, new_controls_block)
    print("Updated top-right-controls to only show toggleAnimalsBtn")

# Remove tweaks panel and tooltip
old_panel = """  <aside class="tweaks-panel glass no-liquid" id="tweaksPanel" aria-label="Tweaks panel">
    <div class="tweaks-header">
      <span class="tweaks-title">Tweaks</span>
      <div class="tweaks-header-actions">
        <button type="button" class="tweaks-chip" id="copyTweaksBtn">Copy</button>
        <button type="button" class="tweaks-chip" id="resetTweaksBtn">Reset</button>
        <button type="button" class="tweaks-close" id="closeTweaksBtn" aria-label="Close tweaks">×</button>
      </div>
    </div>
    <div class="tweaks-body" id="tweaksBody"></div>
  </aside>

  <div class="tweaks-tooltip" id="tweaksTooltip"></div>"""

if old_panel in html:
    html = html.replace(old_panel, '')
    print("Removed tweaksPanel and tweaksTooltip")

with open('template_base.html', 'w', encoding='utf-8') as f:
    f.write(html)


# 2. Update glyph_animals_engine.js to make tweaks element accesses completely null-safe
with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Safe guard tweaks element references
tweaks_setup_old = """  const tweaksOpener = document.getElementById('tweaksOpener');
  const tweaksPanel = document.getElementById('tweaksPanel');
  const tweaksBody = document.getElementById('tweaksBody');
  const tweaksTooltip = document.getElementById('tweaksTooltip');
  const closeTweaksBtn = document.getElementById('closeTweaksBtn');
  const copyTweaksBtn = document.getElementById('copyTweaksBtn');
  const resetTweaksBtn = document.getElementById('resetTweaksBtn');

  let isTweaksOpen = false;
  try {
    isTweaksOpen = localStorage.getItem('wild-tab:tweaks-open') === 'true';
  } catch {}

  function setTweaksOpen(open) {
    isTweaksOpen = open;
    tweaksPanel.classList.toggle('open', open);
    try {
      localStorage.setItem('wild-tab:tweaks-open', open ? 'true' : 'false');
    } catch {}
  }

  tweaksOpener.addEventListener('click', () => setTweaksOpen(true));
  closeTweaksBtn.addEventListener('click', () => setTweaksOpen(false));"""

tweaks_setup_new = """  const tweaksOpener = document.getElementById('tweaksOpener');
  const tweaksPanel = document.getElementById('tweaksPanel');
  const tweaksBody = document.getElementById('tweaksBody');
  const tweaksTooltip = document.getElementById('tweaksTooltip');
  const closeTweaksBtn = document.getElementById('closeTweaksBtn');
  const copyTweaksBtn = document.getElementById('copyTweaksBtn');
  const resetTweaksBtn = document.getElementById('resetTweaksBtn');

  let isTweaksOpen = false;
  try {
    isTweaksOpen = localStorage.getItem('wild-tab:tweaks-open') === 'true';
  } catch {}

  function setTweaksOpen(open) {
    isTweaksOpen = open;
    if (tweaksPanel) tweaksPanel.classList.toggle('open', open);
    try {
      localStorage.setItem('wild-tab:tweaks-open', open ? 'true' : 'false');
    } catch {}
  }

  if (tweaksOpener) tweaksOpener.addEventListener('click', () => setTweaksOpen(true));
  if (closeTweaksBtn) closeTweaksBtn.addEventListener('click', () => setTweaksOpen(false));"""

if tweaks_setup_old in js:
    js = js.replace(tweaks_setup_old, tweaks_setup_new)
    print("Safe-guarded tweaks opener and close button")

# Safe-guard copy and reset listeners
js = js.replace(
    "copyTweaksBtn.addEventListener('click', () => {",
    "if (copyTweaksBtn) copyTweaksBtn.addEventListener('click', () => {"
)
js = js.replace(
    "resetTweaksBtn.addEventListener('click', () => {",
    "if (resetTweaksBtn) resetTweaksBtn.addEventListener('click', () => {"
)

# Safe-guard buildTweaksPanel
js = js.replace(
    "function buildTweaksPanel() {\n    tweaksBody.innerHTML = '';",
    "function buildTweaksPanel() {\n    if (!tweaksBody) return;\n    tweaksBody.innerHTML = '';"
)

with open('glyph_animals_engine.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("glyph_animals_engine.js updated cleanly")
