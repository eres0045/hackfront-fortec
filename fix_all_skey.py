# -*- coding: utf-8 -*-
with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    text = f.read()

target = """function updateAnimal(a, dt, flock) {
    const speciesKey = a.speciesKey || currentSpeciesKey;"""

replacement = """function updateAnimal(a, dt, flock) {
    const speciesKey = a.speciesKey || currentSpeciesKey;
    const sKey = speciesKey;"""

if target in text:
    text = text.replace(target, replacement)
    print("Added sKey to updateAnimal")
else:
    print("Target in updateAnimal not found!")

with open('glyph_animals_engine.js', 'w', encoding='utf-8') as f:
    f.write(text)

print("Saved glyph_animals_engine.js")
