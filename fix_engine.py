# -*- coding: utf-8 -*-
with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix 1: in startleAnimals
old_startle_loop = """    for (let a of currentFlock) {
      const dx = a.x - tapX;
      const dy = a.y - tapY;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 240) {
        const k = 1 - dist / 240;
        if (speciesKey === 'moth') {"""

new_startle_loop = """    for (let a of currentFlock) {
      const dx = a.x - tapX;
      const dy = a.y - tapY;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 240) {
        const k = 1 - dist / 240;
        const sKey = a.speciesKey || currentSpeciesKey;
        if (sKey === 'moth') {"""

if old_startle_loop in text:
    text = text.replace(old_startle_loop, new_startle_loop)
    print("Fixed startle loop header")
else:
    print("Could not find old_startle_loop")

# Replace remaining speciesKey in startleAnimals
text = text.replace("} else if (speciesKey === 'rabbit') {", "} else if (sKey === 'rabbit') {")
text = text.replace("} else if (speciesKey === 'squid') {", "} else if (sKey === 'squid') {")
text = text.replace("} else if (speciesKey === 'owl') {", "} else if (sKey === 'owl') {")
text = text.replace("} else if (speciesKey === 'flyingfish') {", "} else if (sKey === 'flyingfish') {")
text = text.replace("} else if (speciesKey === 'eagle') {", "} else if (sKey === 'eagle') {")

# Fix 2: in drawAnimalEyes
old_eyes = """    if (currentSpeciesKey === 'rabbit') {
      drawEye(0.2, -0.09, 'rgb(255, 230, 220)', '#1a1012');
    } else if (speciesKey === 'seaturtle') {
      drawEye(0.37, 0.045, null, '#0a1410');
      drawEye(0.37, -0.045, null, '#0a1410');
    } else if (speciesKey === 'squid') {
      drawEye(-0.055, 0.06, null, '#2a0a18');
      drawEye(-0.055, -0.06, null, '#2a0a18');
    } else if (speciesKey === 'owl') {
      drawEye(0.135, 0.045, 'rgb(250, 186, 58)', '#0c0704');
      drawEye(0.135, -0.045, 'rgb(250, 186, 58)', '#0c0704');
    } else if (speciesKey === 'flyingfish') {
      drawEye(0.24, 0.032, null, '#08181c');
      drawEye(0.24, -0.032, null, '#08181c');
    } else if (speciesKey === 'eagle') {"""

new_eyes = """    const sKey = a.speciesKey || currentSpeciesKey;
    if (sKey === 'rabbit') {
      drawEye(0.2, -0.09, 'rgb(255, 230, 220)', '#1a1012');
    } else if (sKey === 'seaturtle') {
      drawEye(0.37, 0.045, null, '#0a1410');
      drawEye(0.37, -0.045, null, '#0a1410');
    } else if (sKey === 'squid') {
      drawEye(-0.055, 0.06, null, '#2a0a18');
      drawEye(-0.055, -0.06, null, '#2a0a18');
    } else if (sKey === 'owl') {
      drawEye(0.135, 0.045, 'rgb(250, 186, 58)', '#0c0704');
      drawEye(0.135, -0.045, 'rgb(250, 186, 58)', '#0c0704');
    } else if (sKey === 'flyingfish') {
      drawEye(0.24, 0.032, null, '#08181c');
      drawEye(0.24, -0.032, null, '#08181c');
    } else if (sKey === 'eagle') {"""

if old_eyes in text:
    text = text.replace(old_eyes, new_eyes)
    print("Fixed drawAnimalEyes")
else:
    print("Could not find old_eyes")

with open('glyph_animals_engine.js', 'w', encoding='utf-8') as f:
    f.write(text)

print("Saved glyph_animals_engine.js")
