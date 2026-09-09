#!/usr/bin/env python3
"""Build local player images from explicitly approved image-manifest URLs.

Designed for GitHub Actions. It only downloads entries that have download_url.
It never scrapes a search engine or guesses a source.
"""
from __future__ import annotations
import argparse, json, os, sys, tempfile
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / 'image-manifest.json'
OUT = ROOT / 'images'
MAX_W, MAX_H = 1400, 1800
UA = 'Ari-NBA-Cards/1.0 (+GitHub Actions image builder)'


def download(url: str, path: Path) -> None:
    req = Request(url, headers={'User-Agent': UA})
    with urlopen(req, timeout=40) as r:
        data = r.read()
    path.write_bytes(data)


def process(src: Path, dest: Path) -> tuple[int, int]:
    with Image.open(src) as im:
        im = ImageOps.exif_transpose(im).convert('RGB')
        im.thumbnail((MAX_W, MAX_H), Image.Resampling.LANCZOS)
        dest.parent.mkdir(parents=True, exist_ok=True)
        im.save(dest, 'JPEG', quality=88, optimize=True, progressive=True)
        return im.size


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true', help='redownload existing files')
    args = ap.parse_args()
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    players = data['players']
    OUT.mkdir(exist_ok=True)
    ok = skipped = failed = 0
    failures = []
    for p in players:
        url = p.get('download_url')
        if not url:
            continue
        rel = p['file']
        dest = ROOT / rel
        if dest.exists() and not args.force:
            skipped += 1
            continue
        try:
            with tempfile.TemporaryDirectory() as td:
                raw = Path(td) / 'source'
                download(url, raw)
                w, h = process(raw, dest)
                if min(w, h) < 300:
                    raise ValueError(f'image too small after processing: {w}x{h}')
            print(f'OK   {p["name"]}: {w}x{h}')
            ok += 1
        except Exception as e:
            failed += 1
            failures.append((p['name'], str(e)))
            print(f'FAIL {p["name"]}: {e}')
    print(f'\nDownloaded/processed: {ok}; existing: {skipped}; failed: {failed}')
    if failures:
        print('\nFailures:')
        for name, err in failures:
            print(f'- {name}: {err}')
        return 1
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
