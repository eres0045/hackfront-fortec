import re

# 1. Update template_base.html
with open('template_base.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Update CSS for .composer, .composer-row-1, .composer-row-2, .composer-search-icon, .composer-textarea
css_old_pattern = r'(\.composer\s*\{[^}]*display:\s*flex;[^}]*\})\s*(\.composer:focus-within\s*\{[^}]*\})\s*(\.composer-row-1\s*\{[^}]*\})\s*(\.composer-search-icon\s*\{[^}]*\})\s*(\.composer-textarea\s*\{[^}]*\})\s*(\.composer-textarea::placeholder\s*\{[^}]*\})\s*(\.composer-row-2\s*\{[^}]*\})'

new_css = '''.composer {
      position: relative;
      width: min(var(--composer-width, 720px), calc(100vw - 32px));
      display: flex;
      flex-direction: row;
      align-items: center;
      gap: 12px;
      padding: 8px 10px 8px 18px;
      min-height: 52px;
      border-radius: var(--composer-radius, 28px);
      --blur: 7px;
      --glass-rim: rgba(255,255,255, calc(0.14 * var(--edge)));
      --glass-sheen: rgba(255,255,255, 0.04);
      pointer-events: auto;
      transition: border-color 0.25s ease, box-shadow 0.25s ease, width 0.3s ease, border-radius 0.3s ease;
    }
    .composer:focus-within {
      border-color: rgba(122, 162, 255, calc(0.3 * var(--edge)));
      box-shadow: 0 0 0 3px rgba(122, 162, 255, calc(0.12 * var(--edge))),
                  inset 1px 1px 0 var(--glass-rim),
                  inset -1px -1px 0 var(--glass-rim-low),
                  inset 0 0 24px var(--glass-glow),
                  var(--glass-shadow);
    }
    .composer-search-icon {
      flex-shrink: 0;
      width: 18px;
      height: 18px;
      stroke: #8d8d8d;
    }
    .composer-textarea {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      resize: none;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", 'Geist', system-ui, sans-serif;
      font-size: 15px;
      line-height: 1.45;
      color: #ececec;
      max-height: 160px;
      padding: 4px 0;
      overflow-y: auto;
      user-select: text;
      min-height: 24px;
      height: 24px;
    }
    .composer-textarea::placeholder {
      color: #8d8d8d;
    }'''

# Replace CSS block
if re.search(css_old_pattern, html, flags=re.DOTALL):
    html = re.sub(css_old_pattern, new_css, html, flags=re.DOTALL)
    print("CSS replaced via regex pattern!")
else:
    print("Regex pattern not matched, performing direct string replace...")
    # fallback direct replace
    old_block = """.composer {
      position: relative;
      width: min(var(--composer-width, 720px), calc(100vw - 32px));
      display: flex;
      flex-direction: column;
      gap: 18px;
      padding: 18px 12px 12px 18px;
      border-radius: var(--composer-radius, 24px);
      --blur: 7px;
      --glass-rim: rgba(255,255,255, calc(0.14 * var(--edge)));
      --glass-sheen: rgba(255,255,255, 0.04);
      pointer-events: auto;
      transition: border-color 0.25s ease, box-shadow 0.25s ease, width 0.3s ease, border-radius 0.3s ease;
    }
    .composer:focus-within {
      border-color: rgba(122, 162, 255, calc(0.3 * var(--edge)));
      box-shadow: 0 0 0 3px rgba(122, 162, 255, calc(0.12 * var(--edge))),
                  inset 1px 1px 0 var(--glass-rim),
                  inset -1px -1px 0 var(--glass-rim-low),
                  inset 0 0 24px var(--glass-glow),
                  var(--glass-shadow);
    }
    .composer-row-1 {
      display: flex;
      align-items: flex-start;
      gap: 12px;
    }
    .composer-search-icon {
      flex-shrink: 0;
      width: 18px;
      height: 18px;
      margin-top: 4px;
      stroke: #8d8d8d;
    }
    .composer-textarea {
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      resize: none;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", 'Geist', system-ui, sans-serif;
      font-size: 17px;
      line-height: 1.55;
      color: #ececec;
      max-height: 200px;
      padding: 0;
      overflow-y: auto;
      user-select: text;
    }
    .composer-textarea::placeholder {
      color: #8d8d8d;
    }
    .composer-row-2 {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }"""
    if old_block in html:
        html = html.replace(old_block, new_css)
        print("CSS replaced via direct string match!")
    else:
        print("Warning: old CSS block not found verbatim!")

# Update HTML of composer
html_old_pattern = r'<form class="composer glass" id="composer" onsubmit="return false;">.*?(?=\s*<!-- WhyCode Decision Engine Card -->)'
new_composer_html = '''<form class="composer glass" id="composer" onsubmit="return false;">
      <svg class="composer-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="10.5" cy="10.5" r="6.5"></circle>
        <line x1="15.5" y1="15.5" x2="20.5" y2="20.5"></line>
      </svg>
      <textarea class="composer-textarea" id="composerText" rows="1" placeholder="Ask WhyCode: Why did we make this architectural decision?..."></textarea>

      <div class="composer-actions">
        <button type="button" class="icon-btn-round" id="micBtn" aria-label="Voice input" title="Click to speak your question">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
            <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
            <line x1="12" y1="19" x2="12" y2="23"></line>
            <line x1="8" y1="23" x2="16" y2="23"></line>
          </svg>
        </button>
        <button type="submit" class="send-btn" id="sendBtn" disabled aria-label="Send query">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="19" x2="12" y2="5"></line>
            <polyline points="5 12 12 5 19 12"></polyline>
          </svg>
        </button>
      </div>
'''

if re.search(html_old_pattern, html, flags=re.DOTALL):
    html = re.sub(html_old_pattern, new_composer_html, html, flags=re.DOTALL)
    print("HTML replaced successfully!")
else:
    print("Warning: composer HTML pattern not matched!")

# Also update --composer-radius default in :root
html = html.replace('--composer-radius: 24px;', '--composer-radius: 28px;')

with open('template_base.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 2. Update glyph_animals_engine.js cornerRadius to 28
with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    js = f.read()

js = js.replace('cornerRadius: 24, width: 720', 'cornerRadius: 28, width: 720')

with open('glyph_animals_engine.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Updates to template_base.html and glyph_animals_engine.js finished!")
