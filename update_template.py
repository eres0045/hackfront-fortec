# -*- coding: utf-8 -*-
"""
Updates template_base.html:
- Removes the top species switcher navbar
- Adds top-left WhyCode back button
- Updates page title and search placeholder
"""

with open('template_base.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace title
text = text.replace('<title>glyph animals</title>', '<title>WhyCode — Decision Intelligence</title>')

# Remove <header class="top-bar">...</header> and add WhyCode nav link
p1 = text.find('<header class="top-bar">')
p2 = text.find('</header>') + len('</header>')

if p1 != -1 and p2 != -1:
    back_button = '''  <a href="index.html" class="glass no-liquid" style="position: fixed; top: 16px; left: 16px; z-index: 30; height: 34px; padding: 0 14px 0 12px; border-radius: 999px; font-size: 13px; font-weight: 500; color: var(--text-soft); text-decoration: none; display: inline-flex; align-items: center; gap: 7px; background-color: #0a0c148c; transition: color 0.2s ease;">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="15 18 9 12 15 6"></polyline></svg>
    <span>WhyCode</span>
  </a>'''
    text = text[:p1] + back_button + text[p2:]
    print("Replaced top-bar with WhyCode back button.")
else:
    print("Could not find top-bar block!")

# Update textarea placeholder
text = text.replace('placeholder="Ask anything..."', 'placeholder="Ask WhyCode: Why did we make this architectural decision?..."')

with open('template_base.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("template_base.html updated successfully!")
