# -*- coding: utf-8 -*-
"""
Adds a clean toggle button to turn ON and OFF the appearance of glyph animals.
Persists state in localStorage under 'wild-tab:animals-visible'.
"""

# 1. Update template_base.html
with open('template_base.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add CSS for .toggle-animals-btn
toggle_css = """
    .toggle-animals-btn {
      position: relative;
      height: 34px;
      padding: 0 14px 0 12px;
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
      transition: color 0.2s ease, border-color 0.2s ease, background-color 0.2s ease;
      border: 1px solid var(--chip-edge);
    }
    .toggle-animals-btn:hover {
      color: var(--text);
      border-color: rgba(255, 255, 255, 0.25);
    }
"""

if '.toggle-animals-btn' not in html:
    html = html.replace('.tweaks-opener {', toggle_css + '\n    .tweaks-opener {')

# Replace tweaksOpener with top-right-controls container holding both buttons
old_tweaks_btn = """  <button type="button" class="tweaks-opener glass no-liquid" id="tweaksOpener" aria-label="Open tweaks">
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
  </button>"""

new_controls = """  <div class="top-right-controls" style="position: fixed; top: 16px; right: 16px; z-index: 30; display: flex; gap: 8px; align-items: center;">
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

if old_tweaks_btn in html:
    html = html.replace(old_tweaks_btn, new_controls)
    print("Replaced tweaksOpener with top-right-controls container.")
else:
    print("Could not find old_tweaks_btn in template_base.html")

with open('template_base.html', 'w', encoding='utf-8') as f:
    f.write(html)


# 2. Update glyph_animals_engine.js
with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Add animalsVisible state
visible_init = """  let animalsVisible = true;
  try {
    const saved = localStorage.getItem('wild-tab:animals-visible');
    if (saved !== null) animalsVisible = saved === 'true';
  } catch {}
"""

if 'let animalsVisible' not in js:
    js = js.replace("let currentFlock = [];", "let currentFlock = [];\n" + visible_init)
    print("Added animalsVisible state.")

# In renderFrame, wrap animal rasterization, trails, marine snow, pellets, and eyes in if (animalsVisible)
target_render_start = """    // 3. Rasterize Animals into Cell Buffer
    for (let animal of currentFlock) {"""

new_render_start = """    // 3. Rasterize Animals into Cell Buffer
    if (animalsVisible) {
      for (let animal of currentFlock) {"""

if target_render_start in js:
    js = js.replace(target_render_start, new_render_start)
    print("Added animalsVisible check to start of animal rendering.")

target_render_end = """    // 8. Eyes & Spots Detail Pass
    for (let animal of currentFlock) {
      drawAnimalEyes(animal);
    }
  }"""

new_render_end = """    // 8. Eyes & Spots Detail Pass
      for (let animal of currentFlock) {
        drawAnimalEyes(animal);
      }
    } // end if (animalsVisible)
  }"""

if target_render_end in js:
    js = js.replace(target_render_end, new_render_end)
    print("Closed animalsVisible check in renderFrame.")

# In startleAnimals, skip if !animalsVisible
target_startle = """  function startleAnimals(tapX, tapY) {
    // Stamp a 6-cell trail burst
    stampTrail(tapX, tapY, 3, 1.4);"""

new_startle = """  function startleAnimals(tapX, tapY) {
    if (!animalsVisible) return;
    // Stamp a 6-cell trail burst
    stampTrail(tapX, tapY, 3, 1.4);"""

if target_startle in js:
    js = js.replace(target_startle, new_startle)
    print("Added animalsVisible guard in startleAnimals.")

# Add toggleAnimalsBtn event listener and update function
toggle_listener = """
  // --- UI: Toggle Animals Appearance ---
  const toggleAnimalsBtn = document.getElementById('toggleAnimalsBtn');
  const animalToggleDot = document.getElementById('animalToggleDot');
  const toggleAnimalsText = document.getElementById('toggleAnimalsText');
  const hintEl = document.querySelector('.hint');

  function updateAnimalsVisibilityUI() {
    if (!toggleAnimalsBtn) return;
    if (animalsVisible) {
      toggleAnimalsText.textContent = 'Animals ON';
      toggleAnimalsBtn.style.color = 'var(--text)';
      toggleAnimalsBtn.style.borderColor = 'rgba(74, 222, 128, 0.4)';
      if (animalToggleDot) {
        animalToggleDot.style.background = '#4ade80';
        animalToggleDot.style.boxShadow = '0 0 8px #4ade80';
      }
      if (hintEl) hintEl.style.opacity = '1';
    } else {
      toggleAnimalsText.textContent = 'Animals OFF';
      toggleAnimalsBtn.style.color = 'var(--muted)';
      toggleAnimalsBtn.style.borderColor = 'var(--chip-edge)';
      if (animalToggleDot) {
        animalToggleDot.style.background = '#6b7280';
        animalToggleDot.style.boxShadow = 'none';
      }
      if (hintEl) hintEl.style.opacity = '0';
    }
  }

  if (toggleAnimalsBtn) {
    toggleAnimalsBtn.addEventListener('click', () => {
      animalsVisible = !animalsVisible;
      try {
        localStorage.setItem('wild-tab:animals-visible', animalsVisible ? 'true' : 'false');
      } catch {}
      updateAnimalsVisibilityUI();
      if (isReducedMotion) {
        simulateStillFrame();
      }
    });
  }
"""

if 'updateAnimalsVisibilityUI' not in js:
    js = js.replace("// Load fonts first before starting", toggle_listener + "\n  // Load fonts first before starting")
    js = js.replace("setTweaksOpen(isTweaksOpen);", "setTweaksOpen(isTweaksOpen);\n    updateAnimalsVisibilityUI();")
    print("Added toggleAnimalsBtn listener and initialization.")

with open('glyph_animals_engine.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("glyph_animals_engine.js updated successfully!")
