# Glyph Animals builder script
import base64

with open('geist.woff2.b64', 'r') as f:
    geist_b64 = f.read().strip()
with open('geistmono.woff2.b64', 'r') as f:
    geist_mono_b64 = f.read().strip()

print(f'Loaded fonts: Geist {len(geist_b64)}, GeistMono {len(geist_mono_b64)}')
