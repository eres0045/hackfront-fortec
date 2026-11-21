# -*- coding: utf-8 -*-
import os

with open('template_base.html', 'r', encoding='utf-8') as f:
    template = f.read()

with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    js_engine = f.read()

final_html = template.replace('<!-- SCRIPT_PLACEHOLDER -->', f'<script>\n{js_engine}\n</script>')

with open('glyph_animals.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

with open('query.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print('Generated glyph_animals.html and query.html successfully!')
print(f'File size: {len(final_html)} bytes')
