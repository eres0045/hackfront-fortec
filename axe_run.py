#!/usr/bin/env python3
"""Run real axe-core on the live WhyCode page and print violations."""
import json
import sys

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else (
    "https://whycode-ui.onrender.com/"
    "?q=Why+does+ignore_warnings+match+substrings+by+default")

with sync_playwright() as p:
    browser = p.chromium.launch(args=[
        "--proxy-server=http://127.0.0.1:18080",
        "--ignore-certificate-errors",
    ])
    page = browser.new_page(ignore_https_errors=True)
    page.goto(URL, wait_until="networkidle", timeout=120000)
    page.wait_for_timeout(1500)
    page.add_script_tag(path="/tmp/axe.min.js")
    result = page.evaluate("() => axe.run(document, {resultTypes: ['violations']}).then(r => r.violations)")
    browser.close()

for v in result:
    print(f"== {v['id']} ({v['impact']}) — {v['description']}")
    for n in v["nodes"]:
        print("   html:", n["html"][:220].replace("\n", " "))
        print("   failure:", (n.get("failureSummary") or "")[:300].replace("\n", " "))
    print()
print("TOTAL violations:", len(result))
