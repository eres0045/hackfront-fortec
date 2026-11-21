with open('template_base.html', 'r', encoding='utf-8') as f:
    html = f.read()

old_textarea_css = """.composer-textarea {
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
    }"""

new_textarea_css = """.composer-textarea {
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
      overflow: hidden;
      scrollbar-width: none;
      -ms-overflow-style: none;
      user-select: text;
      min-height: 24px;
      height: 24px;
    }
    .composer-textarea::-webkit-scrollbar {
      display: none;
    }"""

if old_textarea_css in html:
    html = html.replace(old_textarea_css, new_textarea_css)
    print("Replaced textarea CSS successfully in template_base.html")
else:
    print("Could not find exact old_textarea_css block, searching...")

with open('template_base.html', 'w', encoding='utf-8') as f:
    f.write(html)

# Update glyph_animals_engine.js
with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    js = f.read()

old_input_listener = """    composerText.addEventListener('input', () => {
      composerText.style.height = 'auto';
      composerText.style.height = Math.min(200, composerText.scrollHeight) + 'px';
      const hasText = composerText.value.trim().length > 0;
      sendBtn.disabled = !hasText;
      sendBtn.classList.toggle('active', hasText);
    });"""

new_input_listener = """    composerText.addEventListener('input', () => {
      composerText.style.height = 'auto';
      const newHeight = Math.min(160, composerText.scrollHeight);
      composerText.style.height = newHeight + 'px';
      composerText.style.overflowY = composerText.scrollHeight > 160 ? 'auto' : 'hidden';
      const hasText = composerText.value.trim().length > 0;
      sendBtn.disabled = !hasText;
      sendBtn.classList.toggle('active', hasText);
    });"""

if old_input_listener in js:
    js = js.replace(old_input_listener, new_input_listener)
    print("Replaced input listener in glyph_animals_engine.js")

with open('glyph_animals_engine.js', 'w', encoding='utf-8') as f:
    f.write(js)
