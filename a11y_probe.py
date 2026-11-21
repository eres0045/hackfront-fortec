#!/usr/bin/env python3
"""Probe the live WhyCode UI for the two axe findings ArgosX reported:
1. nested interactive controls (an interactive element inside another)
2. text below WCAG 2 AA contrast (4.5:1 normal, 3:1 large)

Loads the live Render URL (the page ArgosX scanned, with an answer shown)
and reports the exact elements, so the fix targets the real ones.
"""
import json
import sys

from playwright.sync_api import sync_playwright

URL = ("https://whycode-ui.onrender.com/"
       "?q=Why+does+ignore_warnings+match+substrings+by+default")

PROBE_JS = """
() => {
  const INTERACTIVE = 'a[href], button, input, select, textarea, [tabindex]';
  const nested = [];
  document.querySelectorAll(INTERACTIVE).forEach(el => {
    let p = el.parentElement;
    while (p) {
      if (p.matches && p.matches(INTERACTIVE)) {
        nested.push({
          el: el.tagName + '.' + (el.className.baseVal !== undefined ? el.className.baseVal : el.className) +
              ' text=' + (el.textContent || '').trim().slice(0, 60),
          ancestor: p.tagName + '.' + (p.className.baseVal !== undefined ? p.className.baseVal : p.className) +
              ' text=' + (p.textContent || '').trim().slice(0, 60),
        });
        break;
      }
      p = p.parentElement;
    }
  });
  function lum(r, g, b) {
    const f = c => { c /= 255; return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
  }
  function parse(c) {
    const m = c.match(/rgba?\\(([^)]+)\\)/);
    if (!m) return null;
    const parts = m[1].split(',').map(Number);
    return { r: parts[0], g: parts[1], b: parts[2], a: parts.length > 3 ? parts[3] : 1 };
  }
  function effBg(el) {
    let node = el;
    while (node) {
      const bg = parse(getComputedStyle(node).backgroundColor);
      if (bg && bg.a > 0) return bg;
      node = node.parentElement;
    }
    return { r: 255, g: 255, b: 255, a: 1 };
  }
  const low = [];
  document.querySelectorAll('body *').forEach(el => {
    const cs = getComputedStyle(el);
    const text = (el.childNodes.length && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) ?
        el.textContent.trim().slice(0, 50) : '';
    if (!text) return;
    const fg = parse(cs.color);
    if (!fg) return;
    let bg = effBg(el);
    if (fg.a < 1) { // blend over bg
      fg.r = Math.round(fg.r * fg.a + bg.r * (1 - fg.a));
      fg.g = Math.round(fg.g * fg.a + bg.g * (1 - fg.a));
      fg.b = Math.round(fg.b * fg.a + bg.b * (1 - fg.a));
    }
    const L1 = lum(fg.r, fg.g, fg.b), L2 = lum(bg.r, bg.g, bg.b);
    const ratio = (Math.max(L1, L2) + 0.05) / (Math.min(L1, L2) + 0.05);
    const size = parseFloat(cs.fontSize);
    const bold = parseInt(cs.fontWeight) >= 700;
    const large = size >= 24 || (size >= 18.66 && bold);
    const need = large ? 3 : 4.5;
    if (ratio < need) {
      low.push({
        el: el.tagName + '.' + (typeof el.className === 'string' ? el.className : ''),
        text, ratio: +ratio.toFixed(2), need,
        fg: cs.color, bg: cs.backgroundColor, size, bold,
      });
    }
  });
  return { nested, low };
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(args=[
        "--proxy-server=http://127.0.0.1:18080",
        "--ignore-certificate-errors",
    ])
    page = browser.new_page(ignore_https_errors=True)
    page.goto(URL, wait_until="networkidle", timeout=120000)
    page.wait_for_timeout(1500)
    result = page.evaluate(PROBE_JS)
    browser.close()

print(json.dumps(result, indent=2))
