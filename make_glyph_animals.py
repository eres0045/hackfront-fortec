# -*- coding: utf-8 -*-
import sys

with open('geist.woff2.b64', 'r', encoding='utf-8') as f:
    geist_b64 = f.read().strip()
with open('geistmono.woff2.b64', 'r', encoding='utf-8') as f:
    geist_mono_b64 = f.read().strip()

print('Font assets loaded.')
