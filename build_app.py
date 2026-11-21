# -*- coding: utf-8 -*-
import os

with open('geist.woff2.b64', 'r', encoding='utf-8') as f:
    geist_b64 = f.read().strip()
with open('geistmono.woff2.b64', 'r', encoding='utf-8') as f:
    geist_mono_b64 = f.read().strip()

print(f"Loaded Geist: {len(geist_b64)} chars, GeistMono: {len(geist_mono_b64)} chars")
