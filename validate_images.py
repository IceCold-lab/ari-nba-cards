#!/usr/bin/env python3
"""Validate that all manifest entries marked required have local images."""
import json, sys
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT/'image-manifest.json').read_text(encoding='utf-8'))
required = [p for p in data['players'] if p.get('required')]
missing=[]; bad=[]
for p in required:
    f=ROOT/p['file']
    if not f.exists():
        missing.append(p['name']); continue
    try:
        with Image.open(f) as im:
            im.verify()
    except Exception as e:
        bad.append((p['name'],str(e)))
print(f'Required images: {len(required)} | missing: {len(missing)} | invalid: {len(bad)}')
if missing:
    print('Missing:'); [print(' -',x) for x in missing]
if bad:
    print('Invalid:'); [print(' -',n,e) for n,e in bad]
sys.exit(1 if missing or bad else 0)
