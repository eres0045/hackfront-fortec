with open('template_base.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add styling to guarantee .top-left-controls children sit side by side
fix_css = """
    .top-left-controls a, .top-left-controls button {
      position: relative !important;
      top: auto !important;
      left: auto !important;
      transform: none !important;
    }
"""

if '.top-left-controls a, .top-left-controls button' not in html:
    html = html.replace('</style>', fix_css + '\n  </style>')
    print("Added top-left flex fix CSS")

with open('template_base.html', 'w', encoding='utf-8') as f:
    f.write(html)

with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Fix quick query cards calling submitQuery directly
old_card_code = """        if (sendBtn) {
          sendBtn.disabled = false;
          sendBtn.classList.add('active');
        }
        submitQuery();"""

new_card_code = """        if (sendBtn) {
          sendBtn.disabled = false;
          sendBtn.classList.add('active');
          sendBtn.click();
        }"""

if old_card_code in js:
    js = js.replace(old_card_code, new_card_code)
    print("Replaced old_card_code with sendBtn.click()")
else:
    print("Searching for quickQueryCards listener...")
    # alternative replacement
    js = js.replace('submitQuery();', 'if (sendBtn) sendBtn.click();')

with open('glyph_animals_engine.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Fix script completed!")
