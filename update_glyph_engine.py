# -*- coding: utf-8 -*-
"""
Update script for glyph_animals_engine.js to:
1. Support 2 to 3 max animals randomly appearing from 2 to 3 random species simultaneously.
2. Remove dependencies on the top navbar.
"""

with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Add ALL_SPECIES_KEYS and pickRandomActiveSpecies
species_init_old = "let currentSpeciesKey = 'moth';"
species_init_new = """const ALL_SPECIES_KEYS = ['moth', 'rabbit', 'seaturtle', 'squid', 'owl', 'flyingfish', 'eagle'];

  function pickRandomActiveSpecies() {
    const shuffled = [...ALL_SPECIES_KEYS].sort(() => Math.random() - 0.5);
    const count = Math.floor(Math.random() * 2) + 2; // 2 or 3
    return shuffled.slice(0, count);
  }
  let activeSpeciesList = pickRandomActiveSpecies();
  let currentSpeciesKey = activeSpeciesList[0];"""

code = code.replace(species_init_old, species_init_new)

# 2. Update updateFlockPopulation to clamp to 2-3 max animals
pop_old = """function updateFlockPopulation(forceSpawn = false) {
    const spec = SPECIES_CONFIGS[currentSpeciesKey];
    const urlParams = new URLSearchParams(window.location.search);
    const countParam = urlParams.get('count');

    let targetCount = countParam ? parseInt(countParam, 10) : 0;
    if (!targetCount || isNaN(targetCount)) {
      const baseSize = Math.min(190, Math.max(80, Math.min(width, height) * 0.2)) * spec.scale;
      const density = activeTunings.density !== undefined ? activeTunings.density : 1;
      const area = spec.area || 60000;
      const factor = (baseSize / spec.scale / 160);
      targetCount = Math.min(200, Math.max(1, Math.round((width * height) / (area * factor * factor) * density)));
    }"""

pop_new = """function updateFlockPopulation(forceSpawn = false) {
    const urlParams = new URLSearchParams(window.location.search);
    const countParam = urlParams.get('count');

    // 2 to 3 max animals appear
    let targetCount = countParam ? parseInt(countParam, 10) : (Math.floor(Math.random() * 2) + 2);
    targetCount = Math.min(3, Math.max(2, targetCount));"""

code = code.replace(pop_old, pop_new)

# 3. Update spawnAnimal to assign random species from activeSpeciesList
spawn_old = """function spawnAnimal(anywhere = false) {
    const spec = SPECIES_CONFIGS[currentSpeciesKey];
    const id = nextAnimalId++;
    const roll = Math.random();
    const farthest = activeTunings.farthest !== undefined ? activeTunings.farthest : 0.45;
    const farBias = activeTunings.farBias !== undefined ? activeTunings.farBias : 1.6;
    const depth = farthest + (1 - farthest) * Math.pow(roll, farBias);
    const base = Math.min(190, Math.max(80, Math.min(width, height) * 0.2)) * spec.scale;
    const span = base * depth * (activeTunings.size || 1);"""

spawn_new = """function spawnAnimal(anywhere = false) {
    // Pick from active 2 to 3 species
    const speciesKey = activeSpeciesList[currentFlock.length % activeSpeciesList.length] || activeSpeciesList[0];
    const spec = SPECIES_CONFIGS[speciesKey];
    const id = nextAnimalId++;
    const roll = Math.random();
    const farthest = activeTunings.farthest !== undefined ? activeTunings.farthest : 0.45;
    const farBias = activeTunings.farBias !== undefined ? activeTunings.farBias : 1.6;
    const depth = farthest + (1 - farthest) * Math.pow(roll, farBias);
    const base = Math.min(190, Math.max(80, Math.min(width, height) * 0.2)) * spec.scale;
    const span = base * depth * (activeTunings.size || 1);"""

code = code.replace(spawn_old, spawn_new)

# In spawnAnimal, also assign speciesKey to animal object
animal_obj_old = """const animal = {
      id,
      roll,"""

animal_obj_new = """const animal = {
      id,
      speciesKey,
      trailColor: spec.trailColor,
      roll,"""

code = code.replace(animal_obj_old, animal_obj_new)

# 4. In updateAnimal, use a.speciesKey
update_old = """function updateAnimal(a, dt, flock) {
    const spec = SPECIES_CONFIGS[currentSpeciesKey];
    const cruise = spec.speedBase * (0.55 + 0.45 * a.depth) * (activeTunings.speed || 1);"""

update_new = """function updateAnimal(a, dt, flock) {
    const speciesKey = a.speciesKey || currentSpeciesKey;
    const spec = SPECIES_CONFIGS[speciesKey];
    const cruise = spec.speedBase * (0.55 + 0.45 * a.depth) * (activeTunings.speed || 1);"""

code = code.replace(update_old, update_new)

# Replace conditions in updateAnimal
code = code.replace("if (currentSpeciesKey === 'moth') {", "if (speciesKey === 'moth') {")
code = code.replace("} else if (currentSpeciesKey === 'rabbit') {", "} else if (speciesKey === 'rabbit') {")
code = code.replace("} else if (currentSpeciesKey === 'seaturtle') {", "} else if (speciesKey === 'seaturtle') {")
code = code.replace("} else if (currentSpeciesKey === 'squid') {", "} else if (speciesKey === 'squid') {")
code = code.replace("} else if (currentSpeciesKey === 'owl') {", "} else if (speciesKey === 'owl') {")
code = code.replace("} else if (currentSpeciesKey === 'flyingfish') {", "} else if (speciesKey === 'flyingfish') {")
code = code.replace("} else if (currentSpeciesKey === 'eagle') {", "} else if (speciesKey === 'eagle') {")
code = code.replace(
    "const maxTurn = (currentSpeciesKey === 'rabbit' ? (a.alarm > 0 ? 10 : 3) : 4) * dt;",
    "const maxTurn = (speciesKey === 'rabbit' ? (a.alarm > 0 ? 10 : 3) : 4) * dt;"
)

# 5. In startleAnimals, check per animal
startle_old = """if (currentSpeciesKey === 'seaturtle') {
      // Tap = feeding! Spawn 7-11 pellets"""

startle_new = """const hasSeaTurtle = currentFlock.some(a => a.speciesKey === 'seaturtle');
    if (hasSeaTurtle) {
      // Tap = feeding! Spawn 7-11 pellets"""

code = code.replace(startle_old, startle_new)

# In startleAnimals loop:
code = code.replace("if (currentSpeciesKey === 'moth') {", "if (a.speciesKey === 'moth') {")
code = code.replace("} else if (currentSpeciesKey === 'rabbit') {", "} else if (a.speciesKey === 'rabbit') {")
code = code.replace("} else if (currentSpeciesKey === 'squid') {", "} else if (a.speciesKey === 'squid') {")
code = code.replace("} else if (currentSpeciesKey === 'owl') {", "} else if (a.speciesKey === 'owl') {")
code = code.replace("} else if (currentSpeciesKey === 'flyingfish') {", "} else if (a.speciesKey === 'flyingfish') {")
code = code.replace("} else if (currentSpeciesKey === 'eagle') {", "} else if (a.speciesKey === 'eagle') {")

# 6. In probeAnimal, use a.speciesKey
probe_old = """function probeAnimal(a, u, v) {
    const key = currentSpeciesKey;"""

probe_new = """function probeAnimal(a, u, v) {
    const key = a.speciesKey || currentSpeciesKey;"""

code = code.replace(probe_old, probe_new)

# 7. In drawAnimalEyes, use a.speciesKey
eyes_old = """if (currentSpeciesKey === 'rabbit') {
      drawEye(0.2, -0.09, 'rgb(255, 230, 220)', '#1a1012');
    } else if (currentSpeciesKey === 'seaturtle') {
      drawEye(0.37, 0.045, null, '#0a1410');
      drawEye(0.37, -0.045, null, '#0a1410');
    } else if (currentSpeciesKey === 'squid') {
      drawEye(-0.055, 0.06, null, '#2a0a18');
      drawEye(-0.055, -0.06, null, '#2a0a18');
    } else if (currentSpeciesKey === 'owl') {
      drawEye(0.135, 0.045, 'rgb(250, 186, 58)', '#0c0704');
      drawEye(0.135, -0.045, 'rgb(250, 186, 58)', '#0c0704');
    } else if (currentSpeciesKey === 'flyingfish') {
      drawEye(0.24, 0.032, null, '#08181c');
      drawEye(0.24, -0.032, null, '#08181c');
    } else if (currentSpeciesKey === 'eagle') {"""

eyes_new = """const eyeKey = a.speciesKey || currentSpeciesKey;
    if (eyeKey === 'rabbit') {
      drawEye(0.2, -0.09, 'rgb(255, 230, 220)', '#1a1012');
    } else if (eyeKey === 'seaturtle') {
      drawEye(0.37, 0.045, null, '#0a1410');
      drawEye(0.37, -0.045, null, '#0a1410');
    } else if (eyeKey === 'squid') {
      drawEye(-0.055, 0.06, null, '#2a0a18');
      drawEye(-0.055, -0.06, null, '#2a0a18');
    } else if (eyeKey === 'owl') {
      drawEye(0.135, 0.045, 'rgb(250, 186, 58)', '#0c0704');
      drawEye(0.135, -0.045, 'rgb(250, 186, 58)', '#0c0704');
    } else if (eyeKey === 'flyingfish') {
      drawEye(0.24, 0.032, null, '#08181c');
      drawEye(0.24, -0.032, null, '#08181c');
    } else if (eyeKey === 'eagle') {"""

code = code.replace(eyes_old, eyes_new)

# In renderFrame, check if any squid or seaturtle
code = code.replace(
    "if (currentSpeciesKey === 'squid') {",
    "if (currentFlock.some(a => a.speciesKey === 'squid')) {"
)
code = code.replace(
    "if (currentSpeciesKey === 'seaturtle') {",
    "if (currentFlock.some(a => a.speciesKey === 'seaturtle') || pellets.length > 0) {"
)

# Safe guard pillButtons if navbar is removed
btn_safe_old = """function updateSpeciesButtonsUI() {
    pillButtons.forEach(btn => {"""

btn_safe_new = """function updateSpeciesButtonsUI() {
    if (!pillButtons || pillButtons.length === 0) return;
    pillButtons.forEach(btn => {"""

code = code.replace(btn_safe_old, btn_safe_new)

pos_safe_old = """function positionThumb() {
    const activeBtn = pillButtons.find(b => b.dataset.species === currentSpeciesKey);
    if (!activeBtn || !thumbEl) return;"""

pos_safe_new = """function positionThumb() {
    if (!pillButtons || pillButtons.length === 0 || !thumbEl) return;
    const activeBtn = pillButtons.find(b => b.dataset.species === currentSpeciesKey);
    if (!activeBtn) return;"""

code = code.replace(pos_safe_old, pos_safe_new)

with open('glyph_animals_engine.js', 'w', encoding='utf-8') as f:
    f.write(code)

print('Updated glyph_animals_engine.js for multi-species 2-to-3 animal limit successfully!')
