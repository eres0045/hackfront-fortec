# Script to generate glyph_animals.html
import json

with open('geist.woff2.b64', 'r', encoding='utf-8') as f:
    geist_b64 = f.read().strip()
with open('geistmono.woff2.b64', 'r', encoding='utf-8') as f:
    geist_mono_b64 = f.read().strip()

print(f'Ready to generate with {len(geist_b64)} bytes of Geist and {len(geist_mono_b64)} bytes of GeistMono')
