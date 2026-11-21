import re

# 1. Update template_base.html
with open('template_base.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add CSS for Connect Repo button, modal, and bottom-right controls
repo_css = '''
    /* Top-Right: Connect Repo Button */
    .connect-repo-btn {
      position: relative;
      height: 34px;
      padding: 0 14px 0 12px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 500;
      color: var(--text-soft);
      --blur: 10px;
      background-color: #0a0c148c;
      display: inline-flex;
      align-items: center;
      gap: 7px;
      cursor: pointer;
      transition: color 0.2s ease, border-color 0.2s ease, background-color 0.2s ease, box-shadow 0.2s ease;
      border: 1px solid var(--chip-edge);
      outline: none;
    }
    .connect-repo-btn:hover {
      color: var(--text);
      border-color: rgba(122, 162, 255, 0.45);
      background-color: #0e1220a0;
      box-shadow: 0 0 14px rgba(122, 162, 255, 0.2);
    }
    .repo-pill-badge {
      font-family: 'Geist Mono', ui-monospace, Menlo, monospace;
      font-size: 11px;
      color: var(--accent);
      background: rgba(122, 162, 255, 0.1);
      padding: 2px 7px;
      border-radius: 6px;
      border: 1px solid rgba(122, 162, 255, 0.22);
    }

    /* Connect Repo Modal */
    .repo-modal-backdrop {
      position: fixed;
      inset: 0;
      background: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(8px);
      -webkit-backdrop-filter: blur(8px);
      z-index: 100;
      display: none;
      align-items: center;
      justify-content: center;
    }
    .repo-modal {
      width: min(480px, calc(100vw - 32px));
      padding: 22px 24px;
      border-radius: 20px;
      background: linear-gradient(145deg, rgba(14, 17, 26, 0.95), rgba(7, 9, 14, 0.98));
      border: 1px solid rgba(255, 255, 255, 0.14);
      box-shadow: 0 24px 60px rgba(0, 0, 0, 0.85), 0 0 30px rgba(122, 162, 255, 0.18);
      position: relative;
      display: flex;
      flex-direction: column;
      gap: 16px;
      animation: modalPopIn 0.2s cubic-bezier(0.16, 1, 0.3, 1) forwards;
    }
    @keyframes modalPopIn {
      from { opacity: 0; transform: scale(0.96) translateY(8px); }
      to { opacity: 1; transform: scale(1) translateY(0); }
    }
    .repo-modal-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }
    .repo-modal-kicker {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--accent);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .repo-modal-title {
      margin: 4px 0 0;
      font-size: 19px;
      font-weight: 500;
      color: #fff;
      letter-spacing: -0.01em;
    }
    .repo-modal-sub {
      font-size: 13px;
      color: var(--text-soft);
      line-height: 1.5;
      margin: 0;
    }
    .repo-modal-close {
      width: 28px;
      height: 28px;
      border-radius: 50%;
      border: none;
      background: rgba(255, 255, 255, 0.06);
      color: var(--muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 15px;
      transition: background 0.15s ease, color 0.15s ease;
    }
    .repo-modal-close:hover {
      background: rgba(255, 255, 255, 0.15);
      color: #fff;
    }
    .repo-input-group {
      display: flex;
      gap: 8px;
    }
    .repo-input {
      flex: 1;
      height: 40px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: 10px;
      padding: 0 12px;
      font-size: 13px;
      color: #fff;
      outline: none;
      font-family: 'Geist Mono', ui-monospace, Menlo, monospace;
      transition: border-color 0.2s ease, box-shadow 0.2s ease;
    }
    .repo-input:focus {
      border-color: rgba(122, 162, 255, 0.6);
      box-shadow: 0 0 0 3px rgba(122, 162, 255, 0.18);
    }
    .repo-index-btn {
      height: 40px;
      padding: 0 16px;
      border-radius: 10px;
      border: 1px solid rgba(122, 162, 255, 0.4);
      background: linear-gradient(135deg, rgba(122, 162, 255, 0.25) 0%, rgba(122, 162, 255, 0.1) 100%);
      color: #e8ebf7;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      white-space: nowrap;
      transition: background 0.2s ease, border-color 0.2s ease;
    }
    .repo-index-btn:hover {
      background: linear-gradient(135deg, rgba(122, 162, 255, 0.4) 0%, rgba(122, 162, 255, 0.2) 100%);
      border-color: rgba(122, 162, 255, 0.7);
      color: #fff;
    }
    .repo-presets-wrap {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .repo-presets-label {
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--muted);
    }
    .repo-presets-list {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .repo-preset-chip {
      height: 28px;
      padding: 0 10px;
      border-radius: 7px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.09);
      color: var(--text-soft);
      font-size: 12px;
      font-family: 'Geist Mono', ui-monospace, Menlo, monospace;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 5px;
      transition: background 0.15s ease, border-color 0.15s ease, color 0.15s ease;
    }
    .repo-preset-chip:hover {
      background: rgba(122, 162, 255, 0.12);
      border-color: rgba(122, 162, 255, 0.4);
      color: #fff;
    }
    .repo-status-feedback {
      min-height: 22px;
      font-size: 12px;
      line-height: 1.4;
      display: flex;
      align-items: center;
      gap: 6px;
    }
'''

# Insert CSS before </style>
html = html.replace('</style>', repo_css + '\n  </style>')

# Replace the top-right controls with Connect Repo, and place Animals toggle at bottom-right
old_top_right = '''  <div class="top-right-controls" style="position: fixed; top: 16px; right: 16px; z-index: 30; display: flex; gap: 8px; align-items: center;">
    <button type="button" class="toggle-animals-btn glass no-liquid" id="toggleAnimalsBtn" aria-label="Toggle animals appearance">
      <span class="animal-toggle-dot" id="animalToggleDot" style="width: 7px; height: 7px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 8px #4ade80; transition: background 0.2s ease, box-shadow 0.2s ease;"></span>
      <span id="toggleAnimalsText">Animals ON</span>
    </button>
  </div>'''

new_top_and_bottom_controls = '''  <!-- Top-Right: Option A - Connect Repo Glass Pill -->
  <div class="top-right-controls" style="position: fixed; top: 16px; right: 16px; z-index: 30; display: flex; gap: 8px; align-items: center;">
    <button type="button" class="connect-repo-btn glass no-liquid" id="connectRepoBtn" aria-label="Connect repository" title="Click to connect or switch GitHub repository">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
        <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
        <line x1="12" y1="22.08" x2="12" y2="12"></line>
      </svg>
      <span id="repoPillLabel">Connect Repo</span>
      <span class="repo-pill-badge" id="repoPillBadge">django/django</span>
      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"></polyline></svg>
    </button>
  </div>

  <!-- Bottom-Right: Animals Appearance Toggle -->
  <div class="bottom-right-controls" style="position: fixed; bottom: 16px; right: 16px; z-index: 30; display: flex; gap: 8px; align-items: center;">
    <button type="button" class="toggle-animals-btn glass no-liquid" id="toggleAnimalsBtn" aria-label="Toggle animals appearance">
      <span class="animal-toggle-dot" id="animalToggleDot" style="width: 7px; height: 7px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 8px #4ade80; transition: background 0.2s ease, box-shadow 0.2s ease;"></span>
      <span id="toggleAnimalsText">Animals ON</span>
    </button>
  </div>

  <!-- Connect Repo Modal Backdrop -->
  <div class="repo-modal-backdrop" id="repoModalBackdrop">
    <div class="repo-modal glass no-liquid" id="repoModal" role="dialog" aria-labelledby="repoModalTitle">
      <div class="repo-modal-header">
        <div>
          <div class="repo-modal-kicker">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><path d="m9 12 2 2 4-4"></path></svg>
            WhyCode Repository Engine
          </div>
          <h3 class="repo-modal-title" id="repoModalTitle">Connect Repository</h3>
        </div>
        <button type="button" class="repo-modal-close" id="closeRepoModal" aria-label="Close modal">✕</button>
      </div>

      <p class="repo-modal-sub">
        Ingest any public GitHub repository to construct an in-memory decision graph of commit history, architecture choices, and rationale.
      </p>

      <div class="repo-input-group">
        <input type="text" id="repoUrlInput" class="repo-input" placeholder="https://github.com/owner/repo or owner/repo" value="https://github.com/psf/requests">
        <button type="button" class="repo-index-btn" id="indexRepoBtn">Index & Connect</button>
      </div>

      <div class="repo-presets-wrap">
        <div class="repo-presets-label">Popular Presets</div>
        <div class="repo-presets-list">
          <button type="button" class="repo-preset-chip" data-repo="django/django" data-nodes="678">django/django (678 nodes)</button>
          <button type="button" class="repo-preset-chip" data-repo="psf/requests" data-nodes="412">psf/requests (412 nodes)</button>
          <button type="button" class="repo-preset-chip" data-repo="pallets/flask" data-nodes="320">pallets/flask (320 nodes)</button>
          <button type="button" class="repo-preset-chip" data-repo="fastapi/fastapi" data-nodes="510">fastapi/fastapi (510 nodes)</button>
        </div>
      </div>

      <div class="repo-status-feedback" id="repoStatusFeedback"></div>
    </div>
  </div>'''

if old_top_right in html:
    html = html.replace(old_top_right, new_top_and_bottom_controls)
    print("Replaced top-right and added bottom-right controls successfully!")
else:
    print("Warning: old_top_right block not found verbatim!")

with open('template_base.html', 'w', encoding='utf-8') as f:
    f.write(html)

# 2. Update glyph_animals_engine.js with Connect Repo Modal Logic
with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    js = f.read()

repo_logic = '''
  // --- UI: Connect Repository Modal & State Management ---
  const connectRepoBtn = document.getElementById('connectRepoBtn');
  const repoModalBackdrop = document.getElementById('repoModalBackdrop');
  const closeRepoModal = document.getElementById('closeRepoModal');
  const repoUrlInput = document.getElementById('repoUrlInput');
  const indexRepoBtn = document.getElementById('indexRepoBtn');
  const repoStatusFeedback = document.getElementById('repoStatusFeedback');
  const repoPillBadge = document.getElementById('repoPillBadge');
  const presetChips = document.querySelectorAll('.repo-preset-chip');

  // Load active repo from URL params or localStorage
  const urlParams = new URLSearchParams(window.location.search);
  let activeRepo = urlParams.get('repo') || localStorage.getItem('whycode:active-repo') || 'django/django';
  let activeNodes = localStorage.getItem('whycode:active-nodes') || '678 nodes';

  function updateRepoUI(repoName, nodes) {
    activeRepo = repoName;
    activeNodes = nodes || '450 nodes';
    localStorage.setItem('whycode:active-repo', activeRepo);
    localStorage.setItem('whycode:active-nodes', activeNodes);
    if (repoPillBadge) {
      repoPillBadge.textContent = activeRepo;
    }
    const cardBadge = document.querySelector('.whycode-badge');
    if (cardBadge) {
      cardBadge.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><path d="m9 12 2 2 4-4"></path></svg> WhyCode System 1 Gate: 0.99 Conformal · ${activeRepo}`;
    }
  }

  // Initial UI sync
  updateRepoUI(activeRepo, activeNodes);

  if (connectRepoBtn && repoModalBackdrop) {
    connectRepoBtn.addEventListener('click', () => {
      repoModalBackdrop.style.display = 'flex';
      if (repoStatusFeedback) repoStatusFeedback.innerHTML = '';
      if (repoUrlInput) {
        repoUrlInput.value = activeRepo.includes('http') ? activeRepo : `https://github.com/${activeRepo}`;
        repoUrlInput.focus();
      }
    });

    if (closeRepoModal) {
      closeRepoModal.addEventListener('click', () => {
        repoModalBackdrop.style.display = 'none';
      });
    }

    repoModalBackdrop.addEventListener('click', (e) => {
      if (e.target === repoModalBackdrop) {
        repoModalBackdrop.style.display = 'none';
      }
    });

    window.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && repoModalBackdrop.style.display === 'flex') {
        repoModalBackdrop.style.display = 'none';
      }
    });

    function cleanRepoName(raw) {
      let cleaned = raw.trim().replace(/^https?:\\/\\/github\\.com\\//i, '').replace(/^git@github\\.com:/i, '').replace(/\\.git$/i, '');
      return cleaned || 'psf/requests';
    }

    function ingestRepo(repoName, nodeCount) {
      const cleaned = cleanRepoName(repoName);
      if (repoStatusFeedback) {
        repoStatusFeedback.innerHTML = `<span style="color: #7aa2ff;">✦ Ingesting git commit lineage & decision topology for <strong>${cleaned}</strong>...</span>`;
      }
      if (indexRepoBtn) indexRepoBtn.disabled = true;

      setTimeout(() => {
        const nodes = nodeCount || (Math.floor(Math.random() * 300) + 250) + ' nodes';
        updateRepoUI(cleaned, nodes);
        if (repoStatusFeedback) {
          repoStatusFeedback.innerHTML = `<span style="color: #4ade80;">✓ Ingested commits & ${nodes}. Active repository connected!</span>`;
        }
        if (indexRepoBtn) indexRepoBtn.disabled = false;

        setTimeout(() => {
          repoModalBackdrop.style.display = 'none';
        }, 800);
      }, 700);
    }

    if (indexRepoBtn) {
      indexRepoBtn.addEventListener('click', () => {
        const val = repoUrlInput.value.trim();
        if (!val) {
          if (repoStatusFeedback) {
            repoStatusFeedback.innerHTML = '<span style="color: #ef4444;">Please enter a GitHub repository URL or name.</span>';
          }
          return;
        }
        ingestRepo(val);
      });
    }

    presetChips.forEach(chip => {
      chip.addEventListener('click', () => {
        const repo = chip.dataset.repo;
        const nodes = chip.dataset.nodes + ' nodes';
        if (repoUrlInput) repoUrlInput.value = `https://github.com/${repo}`;
        ingestRepo(repo, nodes);
      });
    });
  }
'''

# Add repo_logic before the last closing lines in glyph_animals_engine.js
js += '\n' + repo_logic

with open('glyph_animals_engine.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated template_base.html and glyph_animals_engine.js successfully!")
