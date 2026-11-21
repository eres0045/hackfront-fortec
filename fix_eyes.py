# -*- coding: utf-8 -*-
with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    text = f.read()

target = """    if (currentSpeciesKey === 'rabbit') {
      drawEye(0.2, -0.09, 'rgb(255, 230, 220)', '#1a1012');
    } else if (speciesKey === 'seaturtle') {"""

replacement = """    const sKey = a.speciesKey || currentSpeciesKey;
    if (sKey === 'rabbit') {
      drawEye(0.2, -0.09, 'rgb(255, 230, 220)', '#1a1012');
    } else if (sKey === 'seaturtle') {"""

if target in text:
    text = text.replace(target, replacement)
    print("Replaced eye check cleanly!")
else:
    print("Target not found!")

with open('glyph_animals_engine.js', 'w', encoding='utf-8') as f:
    f.write(text)
