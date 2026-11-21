# -*- coding: utf-8 -*-
"""
Generator for glyph_animals.html and query.html.
Embeds fonts as Base64 WOFF2, contains inline CSS and complete procedural JavaScript engine.
"""
import os

with open('geist.woff2.b64', 'r', encoding='utf-8') as f:
    geist_b64 = f.read().strip()
with open('geistmono.woff2.b64', 'r', encoding='utf-8') as f:
    geist_mono_b64 = f.read().strip()

html_template = f'''<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>glyph animals</title>
  <script>
    if (navigator.userAgent.includes("Chrome/")) {{
      document.documentElement.classList.add("liquid");
    }}
  </script>
  <style>
    @font-face {{
      font-family: 'Geist';
      font-style: normal;
      font-weight: 400 500;
      font-display: swap;
      src: url(data:font/woff2;base64,{geist_b64}) format('woff2');
    }}
    @font-face {{
      font-family: 'Geist Mono';
      font-style: normal;
      font-weight: 600;
      font-display: swap;
      src: url(data:font/woff2;base64,{geist_mono_b64}) format('woff2');
    }}

    :root {{
      --bg: #06070c;
      --text: #e8ebf7;
      --text-soft: rgba(232, 235, 247, 0.72);
      --muted: rgba(232, 235, 247, 0.4);
      --tint-a: 0.1;
      --tint-b: 0.03;
      --tint: 0;
      --edge: 0.55;
      --blur: 6px;
      --composer-width: 720px;
      --composer-radius: 24px;

      --glass-edge: rgba(255, 255, 255, calc(0.14 * var(--edge)));
      --glass-rim: rgba(255, 255, 255, calc(0.32 * var(--edge)));
      --glass-rim-low: rgba(255, 255, 255, calc(0.08 * var(--edge)));
      --glass-glow: rgba(140, 170, 255, 0.07);
      --glass-sheen: rgba(255, 255, 255, 0.1);
      --glass-shadow: 0 16px 48px rgba(0,0,0,0.55), 0 2px 8px rgba(0,0,0,0.4);

      --chip: rgba(255, 255, 255, 0.05);
      --chip-hover: rgba(255, 255, 255, 0.12);
      --chip-edge: rgba(255, 255, 255, 0.1);
      --accent: #7aa2ff;
      --thumb: rgba(255, 255, 255, 0.14);
      --focus: rgba(122, 162, 255, 0.3);
    }}

    *, *::before, *::after {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}

    html, body {{
      width: 100%;
      height: 100%;
      background: var(--bg);
      color: var(--text);
      overflow: hidden;
      font-family: 'Geist', ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      -webkit-font-smoothing: antialiased;
      -moz-osx-font-smoothing: grayscale;
      user-select: none;
    }}

    .glass {{
      position: fixed;
      isolation: isolate;
      background: linear-gradient(135deg, rgba(255,255,255, calc(var(--tint-a) * var(--tint))), rgba(255,255,255, calc(var(--tint-b) * var(--tint))));
      border: 1px solid var(--glass-edge);
      box-shadow: inset 1px 1px 0 var(--glass-rim),
                  inset -1px -1px 0 var(--glass-rim-low),
                  inset 0 0 24px var(--glass-glow),
                  var(--glass-shadow);
      backdrop-filter: blur(var(--blur, 6px)) saturate(180%);
      -webkit-backdrop-filter: blur(var(--blur, 6px)) saturate(180%);
      transition: background 0.4s ease, border-color 0.4s ease, box-shadow 0.4s ease;
    }}
    html.liquid .glass:not(.no-liquid) {{
      backdrop-filter: url(#liquid-glass) blur(var(--blur, 6px)) saturate(180%);
      -webkit-backdrop-filter: url(#liquid-glass) blur(var(--blur, 6px)) saturate(180%);
    }}
    .glass::after {{
      content: '';
      position: absolute;
      inset: 0;
      z-index: -1;
      border-radius: inherit;
      background: linear-gradient(180deg, var(--glass-sheen) 0%, transparent 48%);
      pointer-events: none;
    }}

    canvas.field {{
      display: block;
      position: fixed;
      top: 0;
      left: 0;
      width: 100vw;
      height: 100vh;
      touch-action: none;
      font-family: 'Geist Mono', ui-monospace, Menlo, monospace;
      z-index: 1;
    }}

    .top-bar {{
      position: fixed;
      z-index: 30;
      top: 18px;
      left: 50%;
      transform: translateX(-50%);
      display: flex;
      gap: 8px;
      pointer-events: auto;
    }}
    .choices {{
      position: relative;
      display: flex;
      gap: 2px;
      padding: 4px;
      border-radius: 999px;
      --blur: 5px;
      max-width: max(240px, calc(100vw - 300px));
      overflow-x: auto;
      scrollbar-width: none;
    }}
    .choices::-webkit-scrollbar {{
      display: none;
    }}
    .thumb {{
      position: absolute;
      top: 0;
      left: 0;
      height: 32px;
      border-radius: 999px;
      background: var(--thumb);
      box-shadow: inset 0 1px 0 var(--glass-rim), 0 2px 8px rgba(0, 0, 0, 0.12);
      transition: transform 0.35s cubic-bezier(0.3, 1.3, 0.5, 1), width 0.35s cubic-bezier(0.3, 1.3, 0.5, 1);
      pointer-events: none;
      z-index: 1;
    }}
    .pill-btn {{
      position: relative;
      z-index: 2;
      display: inline-flex;
      align-items: center;
      gap: 7px;
      height: 32px;
      padding: 0 13px 0 11px;
      border: none;
      background: transparent;
      color: var(--muted);
      font-family: 'Geist', ui-sans-serif, system-ui, sans-serif;
      font-size: 13px;
      font-weight: 500;
      cursor: pointer;
      transition: color 0.3s ease;
      white-space: nowrap;
      outline: none;
    }}
    .pill-btn:hover {{
      color: var(--text-soft);
    }}
    .pill-btn.active, .pill-btn[aria-checked="true"] {{
      color: var(--text);
    }}
    .pill-dot {{
      width: 9px;
      height: 9px;
      border-radius: 50%;
      flex-shrink: 0;
    }}

    .stage {{
      position: fixed;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      z-index: 20;
      display: flex;
      flex-direction: column;
      align-items: center;
    }}
    .masthead {{
      position: absolute;
      bottom: 100%;
      left: 50%;
      transform: translateX(-50%);
      margin-bottom: 28px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
      pointer-events: none;
    }}
    .avatar {{
      width: 66px;
      height: 66px;
      border-radius: 50%;
      position: relative;
      overflow: hidden;
      background: linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.02) 100%);
      box-shadow: inset 1px 1px 0 var(--glass-rim), 0 8px 24px rgba(0,0,0,0.4);
    }}
    .avatar::before {{
      content: '';
      position: absolute;
      inset: 0;
      border-radius: 50%;
      opacity: 0.62;
      background: repeating-linear-gradient(176deg, rgba(255,255,255,0.2) 0px, rgba(255,255,255,0.2) 2px, rgba(0,0,0,0.25) 2px, rgba(0,0,0,0.25) 5px),
                  radial-gradient(circle at 35% 35%, #9a9ea8 0%, #4a4d55 62%, #24262c 100%);
    }}
    .greeting {{
      margin: 0;
      white-space: nowrap;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", 'Geist', system-ui, sans-serif;
      font-size: clamp(24px, 5vw, 32px);
      font-weight: 500;
      line-height: 1.15;
      letter-spacing: -0.02em;
      color: #e8e8e8;
      text-shadow: 0 0 6px var(--bg), 0 0 24px var(--bg);
    }}
    .composer {{
      position: relative;
      width: min(var(--composer-width, 720px), calc(100vw - 32px));
      display: flex;
      flex-direction: column;
      gap: 18px;
      padding: 18px 12px 12px 18px;
      border-radius: var(--composer-radius, 24px);
      --blur: 7px;
      --glass-rim: rgba(255,255,255, calc(0.14 * var(--edge)));
      --glass-sheen: rgba(255,255,255, 0.04);
      pointer-events: auto;
      transition: border-color 0.25s ease, box-shadow 0.25s ease, width 0.3s ease, border-radius 0.3s ease;
    }}
    .composer:focus-within {{
      border-color: rgba(122, 162, 255, calc(0.3 * var(--edge)));
      box-shadow: 0 0 0 3px rgba(122, 162, 255, calc(0.12 * var(--edge))),
                  inset 1px 1px 0 var(--glass-rim),
                  inset -1px -1px 0 var(--glass-rim-low),
                  inset 0 0 24px var(--glass-glow),
                  var(--glass-shadow);
    }}
    .composer-row-1 {{
      display: flex;
      align-items: flex-start;
      gap: 12px;
    }}
    .composer-search-icon {{
      flex-shrink: 0;
      width: 18px;
      height: 18px;
      margin-top: 4px;
      stroke: #8d8d8d;
    }}
    .composer-textarea {{
      flex: 1;
      background: transparent;
      border: none;
      outline: none;
      resize: none;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", 'Geist', system-ui, sans-serif;
      font-size: 17px;
      line-height: 1.55;
      color: #ececec;
      max-height: 200px;
      padding: 0;
      overflow-y: auto;
      user-select: text;
    }}
    .composer-textarea::placeholder {{
      color: #8d8d8d;
    }}
    .composer-row-2 {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .add-tabs-btn {{
      height: 34px;
      padding: 0 14px 0 11px;
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-radius: 999px;
      background: transparent;
      color: #c4c4c4;
      font-size: 14px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      cursor: pointer;
      transition: background 0.2s ease, color 0.2s ease;
    }}
    .add-tabs-btn:hover {{
      background: rgba(255, 255, 255, 0.05);
      color: #fff;
    }}
    .composer-actions {{
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .icon-btn-round {{
      width: 34px;
      height: 34px;
      border-radius: 50%;
      border: none;
      background: transparent;
      color: #8d8d8d;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      transition: background 0.2s ease, color 0.2s ease;
    }}
    .icon-btn-round:hover {{
      background: rgba(255, 255, 255, 0.06);
      color: #fff;
    }}
    .send-btn {{
      width: 34px;
      height: 34px;
      border-radius: 50%;
      border: none;
      background: #333333;
      color: #7c7c7c;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      cursor: not-allowed;
      transition: background 0.2s ease, color 0.2s ease;
    }}
    .send-btn.active {{
      background: #3a3a3a;
      color: #e6e6e6;
      cursor: pointer;
    }}
    .send-btn.active:hover {{
      background: #f2f2f2;
      color: #1c1c1c;
    }}

    /* WhyCode Intelligent Response Card */
    .whycode-card {{
      position: absolute;
      top: calc(100% + 14px);
      left: 0;
      right: 0;
      border-radius: 20px;
      padding: 18px 20px;
      font-size: 13px;
      line-height: 1.5;
      color: var(--text);
      display: none;
      flex-direction: column;
      gap: 12px;
      box-shadow: 0 20px 50px rgba(0,0,0,0.6);
      z-index: 35;
      animation: fadeInCard 0.25s ease forwards;
    }}
    @keyframes fadeInCard {{
      from {{ opacity: 0; transform: translateY(-8px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .whycode-card-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 1px solid var(--chip-edge);
      padding-bottom: 8px;
    }}
    .whycode-badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--accent);
      background: rgba(122, 162, 255, 0.1);
      padding: 3px 8px;
      border-radius: 6px;
      border: 1px solid rgba(122, 162, 255, 0.25);
    }}
    .whycode-close-btn {{
      background: transparent;
      border: none;
      color: var(--muted);
      cursor: pointer;
      font-size: 16px;
    }}
    .whycode-close-btn:hover {{
      color: var(--text);
    }}

    .hint {{
      position: fixed;
      left: 14px;
      bottom: 12px;
      font-family: 'Geist Mono', ui-monospace, Menlo, monospace;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.02em;
      color: var(--muted);
      pointer-events: none;
      user-select: none;
      z-index: 10;
    }}

    .tweaks-opener {{
      position: fixed;
      top: 16px;
      right: 16px;
      z-index: 30;
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
      transition: color 0.2s ease;
    }}
    .tweaks-opener:hover {{
      color: var(--text);
    }}
    .tweaks-panel {{
      position: fixed;
      top: 16px;
      right: 16px;
      z-index: 40;
      width: 288px;
      max-height: calc(100vh - 32px);
      border-radius: 20px;
      font-size: 12px;
      --blur: 18px;
      background-color: #0a0c14c0;
      display: flex;
      flex-direction: column;
      opacity: 0;
      pointer-events: none;
      transform: scale(0.96) translateY(-4px);
      transition: opacity 0.25s ease, transform 0.25s ease;
      box-shadow: 0 24px 64px rgba(0,0,0,0.7), 0 2px 12px rgba(0,0,0,0.5);
    }}
    .tweaks-panel.open {{
      opacity: 1;
      pointer-events: auto;
      transform: scale(1) translateY(0);
    }}
    .tweaks-header {{
      padding: 12px 10px 10px 16px;
      border-bottom: 1px solid var(--chip-edge);
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }}
    .tweaks-title {{
      font-size: 13px;
      font-weight: 500;
      color: var(--text);
    }}
    .tweaks-header-actions {{
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .tweaks-chip {{
      height: 26px;
      padding: 0 10px;
      border-radius: 999px;
      border: 1px solid var(--chip-edge);
      background: var(--chip);
      color: var(--text-soft);
      font-size: 11px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      transition: all 0.15s ease;
    }}
    .tweaks-chip:hover {{
      background: var(--chip-hover);
      color: var(--text);
    }}
    .tweaks-chip.danger {{
      color: #ff6b6b;
      border-color: rgba(255, 107, 107, 0.4);
    }}
    .tweaks-close {{
      width: 26px;
      height: 26px;
      border-radius: 50%;
      border: none;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 16px;
      line-height: 1;
      transition: color 0.15s ease;
    }}
    .tweaks-close:hover {{
      color: var(--text);
    }}
    .tweaks-body {{
      padding: 4px 16px 14px;
      overflow-y: auto;
      overscroll-behavior: contain;
      flex: 1;
    }}
    .tweaks-group-title {{
      font-family: 'Geist Mono', ui-monospace, Menlo, monospace;
      font-size: 10px;
      font-weight: 600;
      letter-spacing: 0.08em;
      color: var(--muted);
      text-transform: uppercase;
      margin: 14px 0 6px;
    }}
    .tweaks-row {{
      display: grid;
      grid-template-columns: 1fr auto;
      grid-template-rows: auto auto;
      row-gap: 4px;
      margin-bottom: 10px;
      position: relative;
    }}
    .tweaks-row.disabled {{
      opacity: 0.4;
      pointer-events: none;
    }}
    .tweaks-label {{
      font-size: 12px;
      color: var(--text-soft);
      cursor: pointer;
      user-select: none;
    }}
    .tweaks-val {{
      font-family: 'Geist Mono', ui-monospace, Menlo, monospace;
      font-size: 11px;
      font-weight: 600;
      color: var(--text);
      text-align: right;
    }}
    .tweaks-slider-container {{
      grid-column: 1 / -1;
      display: flex;
      align-items: center;
      height: 18px;
    }}
    .tweaks-slider {{
      -webkit-appearance: none;
      appearance: none;
      width: 100%;
      height: 4px;
      border-radius: 2px;
      outline: none;
      background: linear-gradient(to right, var(--accent) 0%, var(--accent) var(--fill, 50%), var(--chip-edge) var(--fill, 50%), var(--chip-edge) 100%);
      cursor: pointer;
    }}
    .tweaks-slider::-webkit-slider-thumb {{
      -webkit-appearance: none;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #ffffff;
      border: 1px solid rgba(0,0,0,0.15);
      box-shadow: 0 1px 4px rgba(0,0,0,0.4);
      cursor: pointer;
    }}
    .tweaks-toggle {{
      position: relative;
      width: 30px;
      height: 18px;
      background: var(--chip-edge);
      border-radius: 999px;
      cursor: pointer;
      transition: background 0.2s ease;
    }}
    .tweaks-toggle.checked {{
      background: var(--accent);
    }}
    .tweaks-toggle-knob {{
      position: absolute;
      top: 2px;
      left: 2px;
      width: 14px;
      height: 14px;
      border-radius: 50%;
      background: #ffffff;
      transition: transform 0.2s cubic-bezier(0.3, 1.3, 0.5, 1);
      box-shadow: 0 1px 3px rgba(0,0,0,0.3);
    }}
    .tweaks-toggle.checked .tweaks-toggle-knob {{
      transform: translateX(12px);
    }}
    .tweaks-tooltip {{
      position: fixed;
      z-index: 50;
      max-width: 240px;
      background: #0e101aeb;
      border: 1px solid var(--chip-edge);
      padding: 8px 12px;
      border-radius: 12px;
      font-size: 11px;
      line-height: 1.4;
      color: var(--text);
      box-shadow: 0 8px 24px rgba(0,0,0,0.5);
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.15s ease;
    }}
    .tweaks-tooltip.visible {{
      opacity: 1;
    }}

    /* Responsive Breakpoints */
    @media (max-width: 920px) {{
      .choices {{
        flex-wrap: wrap;
        justify-content: center;
        row-gap: 2px;
        overflow: visible;
        border-radius: 22px;
        max-width: calc(100vw - 32px);
      }}
    }}
    @media (max-width: 720px) {{
      .top-bar {{
        left: 12px;
        right: 12px;
        top: max(12px, env(safe-area-inset-top));
        transform: none;
        width: auto;
      }}
      .tweaks-opener {{
        top: auto;
        bottom: max(12px, env(safe-area-inset-bottom));
        right: 12px;
      }}
      .tweaks-panel {{
        top: auto;
        left: 12px;
        right: 12px;
        bottom: 12px;
        width: auto;
        max-height: 70vh;
        border-radius: 20px;
      }}
      .hint {{
        bottom: max(22px, calc(env(safe-area-inset-bottom) + 10px));
      }}
    }}
    @media (max-width: 640px) {{
      .pill-btn {{
        height: 30px;
        padding: 0 11px 0 9px;
        gap: 6px;
        font-size: 12.5px;
      }}
      .thumb {{
        height: 30px;
      }}
    }}
    @media (max-width: 520px) {{
      .add-tabs-label {{
        display: none;
      }}
      .add-tabs-btn {{
        padding: 0 9px;
      }}
    }}
    @media (max-width: 360px) {{
      .pill-btn {{
        padding: 0 8px 0 7px;
        gap: 5px;
        font-size: 12px;
      }}
    }}
    @media (max-width: 640px) and (min-height: 521px) and (max-height: 700px) {{
      .avatar {{
        width: 48px;
        height: 48px;
      }}
      .masthead {{
        gap: 10px;
        margin-bottom: 18px;
      }}
      .stage {{
        transform: translate(-50%, calc(-50% + 30px));
      }}
    }}
    @media (max-height: 520px) {{
      .avatar {{
        display: none;
      }}
      .masthead {{
        gap: 8px;
        margin-bottom: 14px;
      }}
      .greeting {{
        font-size: 22px;
      }}
      .composer {{
        gap: 10px;
        padding: 12px 10px 10px 14px;
      }}
      .top-bar {{
        top: max(8px, env(safe-area-inset-top));
      }}
      .stage {{
        transform: translate(-50%, calc(-50% + 24px));
      }}
    }}
    @media (prefers-reduced-motion: reduce) {{
      *, *::before, *::after {{
        transition: none !important;
        animation: none !important;
      }}
    }}
  </style>
</head>
<body>
  <svg style="position:fixed;width:0;height:0;pointer-events:none;overflow:hidden;" aria-hidden="true">
    <defs>
      <filter id="liquid-glass" x="0%" y="0%" width="100%" height="100%" color-interpolation-filters="sRGB">
        <feTurbulence id="turb" type="fractalNoise" baseFrequency="0.007 0.011" numOctaves="2" seed="11" result="noise" />
        <feGaussianBlur stdDeviation="2" result="blurNoise" />
        <feDisplacementMap id="disp" in="SourceGraphic" in2="blurNoise" scale="40" xChannelSelector="R" yChannelSelector="G" />
      </filter>
    </defs>
  </svg>

  <canvas class="field" aria-hidden="true"></canvas>

  <header class="top-bar">
    <div class="choices glass" role="radiogroup" aria-label="Animal">
      <span class="thumb"></span>
      <button class="pill-btn active" role="radio" aria-checked="true" tabindex="0" data-species="moth">
        <span class="pill-dot" style="background: radial-gradient(circle at 35% 30%, rgb(244,209,190) 0%, rgb(232,162,124) 70%);"></span>
        <span>Moth</span>
      </button>
      <button class="pill-btn" role="radio" aria-checked="false" tabindex="-1" data-species="rabbit">
        <span class="pill-dot" style="background: radial-gradient(circle at 35% 30%, rgb(252,227,218) 0%, rgb(248,199,181) 70%);"></span>
        <span>Rabbit</span>
      </button>
      <button class="pill-btn" role="radio" aria-checked="false" tabindex="-1" data-species="seaturtle">
        <span class="pill-dot" style="background: radial-gradient(circle at 35% 30%, rgb(182,216,197) 0%, rgb(109,176,138) 70%);"></span>
        <span>Sea turtle</span>
      </button>
      <button class="pill-btn" role="radio" aria-checked="false" tabindex="-1" data-species="squid">
        <span class="pill-dot" style="background: radial-gradient(circle at 35% 30%, rgb(244,181,208) 0%, rgb(232,106,160) 70%);"></span>
        <span>Squid</span>
      </button>
      <button class="pill-btn" role="radio" aria-checked="false" tabindex="-1" data-species="owl">
        <span class="pill-dot" style="background: radial-gradient(circle at 35% 30%, rgb(236,225,208) 0%, rgb(217,195,160) 70%);"></span>
        <span>Owl</span>
      </button>
      <button class="pill-btn" role="radio" aria-checked="false" tabindex="-1" data-species="flyingfish">
        <span class="pill-dot" style="background: radial-gradient(circle at 35% 30%, rgb(194,241,238) 0%, rgb(133,227,221) 70%);"></span>
        <span>Flying fish</span>
      </button>
      <button class="pill-btn" role="radio" aria-checked="false" tabindex="-1" data-species="eagle">
        <span class="pill-dot" style="background: radial-gradient(circle at 35% 30%, rgb(243,244,249) 0%, rgb(230,233,242) 70%);"></span>
        <span>Eagle</span>
      </button>
    </div>
  </header>

  <main class="stage">
    <div class="masthead">
      <div class="avatar glass"></div>
      <h1 class="greeting" id="greeting">Good morning, Rosalie</h1>
    </div>

    <form class="composer glass" id="composer" onsubmit="return false;">
      <div class="composer-row-1">
        <svg class="composer-search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="10.5" cy="10.5" r="6.5"></circle>
          <line x1="15.5" y1="15.5" x2="20.5" y2="20.5"></line>
        </svg>
        <textarea class="composer-textarea" id="composerText" rows="1" placeholder="Ask anything..."></textarea>
      </div>

      <div class="composer-row-2">
        <button type="button" class="add-tabs-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="12" y1="5" x2="12" y2="19"></line>
            <line x1="5" y1="12" x2="19" y2="12"></line>
          </svg>
          <span class="add-tabs-label">Add tabs or files</span>
        </button>

        <div class="composer-actions">
          <button type="button" class="icon-btn-round" aria-label="Voice input">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
              <line x1="12" y1="19" x2="12" y2="23"></line>
              <line x1="8" y1="23" x2="16" y2="23"></line>
            </svg>
          </button>
          <button type="submit" class="send-btn" id="sendBtn" disabled aria-label="Send query">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="19" x2="12" y2="5"></line>
              <polyline points="5 12 12 5 19 12"></polyline>
            </svg>
          </button>
        </div>
      </div>

      <!-- WhyCode Decision Engine Card -->
      <div class="whycode-card glass no-liquid" id="whycodeCard">
        <div class="whycode-card-header">
          <div class="whycode-badge">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"></circle><path d="m9 12 2 2 4-4"></path></svg>
            WhyCode System 1 Gate: 0.99 Conformal
          </div>
          <button type="button" class="whycode-close-btn" id="closeWhyCodeCard" aria-label="Close">✕</button>
        </div>
        <div id="whycodeOutput"></div>
      </div>
    </form>
  </main>

  <p class="hint">click to scatter</p>

  <button type="button" class="tweaks-opener glass no-liquid" id="tweaksOpener" aria-label="Open tweaks">
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="4" y1="21" x2="4" y2="14"></line>
      <line x1="4" y1="10" x2="4" y2="3"></line>
      <line x1="12" y1="21" x2="12" y2="12"></line>
      <line x1="12" y1="8" x2="12" y2="3"></line>
      <line x1="20" y1="21" x2="20" y2="16"></line>
      <line x1="20" y1="12" x2="20" y2="3"></line>
      <line x1="1" y1="14" x2="7" y2="14"></line>
      <line x1="9" y1="8" x2="15" y2="8"></line>
      <line x1="17" y1="16" x2="23" y2="16"></line>
    </svg>
    <span>Tweaks</span>
  </button>

  <aside class="tweaks-panel glass no-liquid" id="tweaksPanel" aria-label="Tweaks panel">
    <div class="tweaks-header">
      <span class="tweaks-title">Tweaks</span>
      <div class="tweaks-header-actions">
        <button type="button" class="tweaks-chip" id="copyTweaksBtn">Copy</button>
        <button type="button" class="tweaks-chip" id="resetTweaksBtn">Reset</button>
        <button type="button" class="tweaks-close" id="closeTweaksBtn" aria-label="Close tweaks">×</button>
      </div>
    </div>
    <div class="tweaks-body" id="tweaksBody"></div>
  </aside>

  <div class="tweaks-tooltip" id="tweaksTooltip"></div>

  <!-- SCRIPT_PLACEHOLDER -->
</body>
</html>
'''

with open('template_base.html', 'w', encoding='utf-8') as f:
    f.write(html_template)

print('template_base.html created')
