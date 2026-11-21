# -*- coding: utf-8 -*-
"""
1. Removes 'Add tabs or files' button.
2. Replaces it with a sleek repo badge 'django/django · 678 nodes'.
3. Adds real working Web Speech Recognition to the mic button with pulsating recording animation.
"""

# 1. Update template_base.html
with open('template_base.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add recording animation CSS
mic_css = """
    .icon-btn-round.recording {
      color: #ef4444 !important;
      background: rgba(239, 68, 68, 0.15) !important;
      border: 1px solid rgba(239, 68, 68, 0.4) !important;
      box-shadow: 0 0 14px rgba(239, 68, 68, 0.45) !important;
      animation: micPulse 1.2s infinite ease-in-out;
    }
    @keyframes micPulse {
      0%, 100% { transform: scale(1); box-shadow: 0 0 8px rgba(239, 68, 68, 0.3); }
      50% { transform: scale(1.08); box-shadow: 0 0 18px rgba(239, 68, 68, 0.6); }
    }
"""

if '.icon-btn-round.recording' not in html:
    html = html.replace('.send-btn {', mic_css + '\n    .send-btn {')
    print("Added mic recording CSS.")

# Replace composer-row-2 contents
old_row2 = """      <div class="composer-row-2">
        <button type="button" class="add-tabs-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span class="add-tabs-label">Add tabs or files</span>
        </button>

        <div class="composer-actions">
          <button type="button" class="icon-btn-round" aria-label="Voice input">"""

new_row2 = """      <div class="composer-row-2">
        <div class="composer-repo-badge" style="display: inline-flex; align-items: center; gap: 6px; font-size: 12px; font-family: 'Geist Mono', monospace; color: var(--muted); user-select: none;">
          <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--accent); box-shadow: 0 0 8px var(--accent);"></span>
          <span>django/django · 678 nodes</span>
        </div>

        <div class="composer-actions">
          <button type="button" class="icon-btn-round" id="micBtn" aria-label="Voice input" title="Click to speak your question">"""

if old_row2 in html:
    html = html.replace(old_row2, new_row2)
    print("Replaced add-tabs-btn with repo badge and added id='micBtn'")
else:
    print("Could not find old_row2 in template_base.html!")

with open('template_base.html', 'w', encoding='utf-8') as f:
    f.write(html)


# 2. Update glyph_animals_engine.js
with open('glyph_animals_engine.js', 'r', encoding='utf-8') as f:
    js = f.read()

voice_code = """
  // --- UI: Working Real Voice Input (Web Speech Recognition) ---
  const micBtn = document.getElementById('micBtn');
  let recognition = null;
  let isRecording = false;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  if (micBtn) {
    if (SpeechRecognition) {
      recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onstart = () => {
        isRecording = true;
        micBtn.classList.add('recording');
        micBtn.setAttribute('aria-label', 'Listening... click to stop');
        composerText.placeholder = 'Listening for your question... speak now';
      };

      recognition.onresult = (e) => {
        let transcript = '';
        for (let i = e.resultIndex; i < e.results.length; ++i) {
          transcript += e.results[i][0].transcript;
        }
        composerText.value = transcript;
        composerText.style.height = 'auto';
        composerText.style.height = Math.min(200, composerText.scrollHeight) + 'px';
        const hasText = composerText.value.trim().length > 0;
        sendBtn.disabled = !hasText;
        sendBtn.classList.toggle('active', hasText);
      };

      recognition.onerror = (e) => {
        console.warn('Speech recognition error:', e.error);
        stopRecording();
        if (e.error === 'not-allowed') {
          composerText.placeholder = 'Microphone access blocked. Type your question instead.';
          setTimeout(() => {
            composerText.placeholder = 'Ask WhyCode: Why did we make this architectural decision?...';
          }, 4000);
        }
      };

      recognition.onend = () => {
        stopRecording();
      };

      function stopRecording() {
        isRecording = false;
        micBtn.classList.remove('recording');
        micBtn.setAttribute('aria-label', 'Voice input');
        composerText.placeholder = 'Ask WhyCode: Why did we make this architectural decision?...';
      }

      micBtn.addEventListener('click', () => {
        if (isRecording) {
          recognition.stop();
        } else {
          try {
            recognition.start();
          } catch (err) {
            console.warn('Could not start recognition:', err);
          }
        }
      });
    } else {
      micBtn.title = 'Speech Recognition is not supported by this browser';
      micBtn.addEventListener('click', () => {
        composerText.placeholder = 'Speech recognition requires Chrome, Chromium, or Edge.';
        setTimeout(() => {
          composerText.placeholder = 'Ask WhyCode: Why did we make this architectural decision?...';
        }, 3500);
      });
    }
  }
"""

if 'const SpeechRecognition' not in js:
    # Insert right before "// --- UI: Tweaks Panel Construction ---" or at end of composer setup
    js = js.replace("composerForm.addEventListener('submit'", voice_code + "\n  composerForm.addEventListener('submit'")
    print("Added Web Speech Recognition logic to glyph_animals_engine.js.")

with open('glyph_animals_engine.js', 'w', encoding='utf-8') as f:
    f.write(js)

print("glyph_animals_engine.js updated successfully!")
