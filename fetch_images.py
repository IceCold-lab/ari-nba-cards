#!/usr/bin/env python3
"""Build local player images from image-approvals.json, with image-manifest fallback.

Approved crops are non-destructive: the original source is downloaded to a temp file,
then a 3:4 crop is applied with Pillow and the derived local JPEG is written to images/.
"""
from __future__ import annotations
import argparse, json, os, sys, tempfile, time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
APPROVALS = ROOT / 'approved-images.json'
MANIFEST = ROOT / 'image-manifest.json'
OUT = ROOT / 'images'
MAX_W, MAX_H = 1200, 1600
ASPECT_W, ASPECT_H = 3, 4
UA = 'Ari-NBA-Cards/1.1 (+GitHub Actions image builder)'

def download(url: str, path: Path) -> None:
    for attempt in range(5):
        req = Request(url, headers={'User-Agent': UA})
        try:
            with urlopen(req, timeout=40) as r:
                path.write_bytes(r.read())
            return
        except HTTPError as e:
            if e.code not in (429, 503):
                raise
            retry_after = e.headers.get('Retry-After')
            try: wait = max(5, int(retry_after)) if retry_after else min(60, 5 * (2 ** attempt))
            except ValueError: wait = 10
            print(f'  Rate limit ({e.code}); waiting {wait}s...')
            time.sleep(wait)
    raise RuntimeError('source remained rate-limited after 5 attempts')

def crop_34(im: Image.Image, zoom: float, x: float, y: float) -> Image.Image:
    w, h = im.size
    base_w = min(w, h * ASPECT_W / ASPECT_H)
    base_h = base_w * ASPECT_H / ASPECT_W
    crop_w = base_w / max(1.0, float(zoom))
    crop_h = base_h / max(1.0, float(zoom))
    max_x = max(0.0, w - crop_w)
    max_y = max(0.0, h - crop_h)
    left = max_x * max(0.0, min(100.0, float(x))) / 100.0
    top = max_y * max(0.0, min(100.0, float(y))) / 100.0
    box = (round(left), round(top), round(left + crop_w), round(top + crop_h))
    return im.crop(box)

def process(src: Path, dest: Path, crop: dict | None) -> tuple[int,int]:
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert('RGB')
        if crop:
            im = crop_34(im, crop.get('zoom', 1), crop.get('x', 50), crop.get('y', 50))
        # Fit exactly into the canonical portrait bounds without distortion.
        im.thumbnail((MAX_W, MAX_H), Image.Resampling.LANCZOS)
        # Ensure final ratio is exactly 3:4 by a final centered trim only for rounding.
        target_ratio = ASPECT_W / ASPECT_H
        w,h=im.size
        if abs((w/h)-target_ratio) > 1e-3:
            target_h=round(w/target_ratio)
            if target_h <= h:
                top=(h-target_h)//2
                im=im.crop((0,top,w,top+target_h))
            else:
                target_w=round(h*target_ratio)
                left=(w-target_w)//2
                im=im.crop((left,0,left+target_w,h))
        # Normalize to a predictable output size.
        im=im.resize((900,1200), Image.Resampling.LANCZOS)
        dest.parent.mkdir(parents=True,exist_ok=True)
        im.save(dest,'JPEG',quality=88,optimize=True,progressive=True)
        return im.size

def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--force',action='store_true')
    args=ap.parse_args()

    approved = {}
    if APPROVALS.exists():
        approved=json.loads(APPROVALS.read_text(encoding='utf-8')).get('players',{})
    manifest = {}
    if MANIFEST.exists():
        manifest=json.loads(MANIFEST.read_text(encoding='utf-8')).get('players',[])
    manifest_by_id={p.get('id'):p for p in manifest}

    jobs=[]
    for pid,a in approved.items():
        src=a.get('original') or a.get('url')
        if src:
            jobs.append((pid,a.get('name',pid),src,a.get('crop')))
    # Preserve existing manifest fallback for players not yet approved.
    for pid,p in manifest_by_id.items():
        if pid not in approved and p.get('download_url'):
            jobs.append((pid,p.get('name',pid),p['download_url'],None))

    OUT.mkdir(exist_ok=True)
    ok=skipped=failed=0
    failures=[]
    for pid,name,url,crop in jobs:
        dest=OUT/f'{pid}.jpg'
        if dest.exists() and not args.force:
            skipped+=1
            continue
        try:
            with tempfile.TemporaryDirectory() as td:
                raw=Path(td)/'source'
                download(url,raw)
                w,h=process(raw,dest,crop)
                if (w,h)!=(900,1200):
                    raise ValueError(f'unexpected output dimensions: {w}x{h}')
            print(f'OK   {name}: {w}x{h}')
            ok+=1
        except Exception as e:
            failed+=1
            failures.append((name,str(e)))
            print(f'FAIL {name}: {e}')
    print(f'\nProcessed: {ok}; existing: {skipped}; failed: {failed}')
    if failures:
        print('\nFailures:')
        for name,err in failures: print(f'- {name}: {err}')
        return 1
    return 0

if __name__=='__main__':
    raise SystemExit(main())
