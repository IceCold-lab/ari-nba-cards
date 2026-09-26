#!/usr/bin/env python3
"""Build local player images from image-approvals.json.

IMPORTANT: image-approvals.json stores the selected candidate by index in
player["selected"], not as player["url"]. This script resolves that candidate
explicitly, so the production image is the exact image approved in the reviewer.
"""
from __future__ import annotations

import argparse
import json
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent
APPROVALS = ROOT / "image-approvals.json"
APPROVED_ALT = ROOT / "approved-images.json"
MANIFEST = ROOT / "image-manifest.json"
OUT = ROOT / "images"

OUTPUT_SIZE = (900, 1200)
ASPECT = 3 / 4
DOWNLOAD_TIMEOUT = 40
MAX_DOWNLOAD_BYTES = 25 * 1024 * 1024
UA = "Ari-NBA-Cards/1.3 (+GitHub Actions image builder)"
CHUNK_SIZE = 1024 * 1024


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def selected_candidate(player: dict) -> tuple[dict | None, int | None]:
    """Resolve the exact candidate selected in the reviewer."""
    candidates = player.get("candidates") or []
    selected = player.get("selected")

    if isinstance(selected, int) and 0 <= selected < len(candidates):
        return candidates[selected], selected

    # Backward-compatible fallback: locate the candidate explicitly marked keep.
    decisions = player.get("candidateDecisions") or {}
    for i, candidate in enumerate(candidates):
        original = candidate.get("original")
        url = candidate.get("url")
        if original and decisions.get(original) == "keep":
            return candidate, i
        if url and decisions.get(url) == "keep":
            return candidate, i

    return None, None


def source_url(candidate: dict) -> str | None:
    # Prefer the reviewer's 960px thumbnail for Wikimedia candidates.
    # The output is only 900x1200, so the full original is unnecessary.
    return candidate.get("url") or candidate.get("original")


def crop_for_selected(player: dict, selected_index: int | None) -> dict | None:
    crops = player.get("crops") or {}
    if selected_index is not None:
        crop = crops.get(str(selected_index))
        if crop:
            return crop
        crop = crops.get(selected_index)
        if crop:
            return crop

    # Fallback for the alternate approval format.
    crop = player.get("crop")
    return crop if isinstance(crop, dict) else None


def download(url: str, path: Path) -> None:
    last_error = None

    for attempt in range(5):
        req = Request(
            url,
            headers={
                "User-Agent": UA,
                "Accept": "image/avif,image/webp,image/jpeg,image/png,*/*;q=0.8",
            },
        )

        try:
            with urlopen(req, timeout=DOWNLOAD_TIMEOUT) as response:
                length = response.headers.get("Content-Length")
                if length and int(length) > MAX_DOWNLOAD_BYTES:
                    raise RuntimeError(
                        f"source is too large ({int(length) / 1048576:.1f} MB)"
                    )

                total = 0
                with path.open("wb") as output:
                    while True:
                        chunk = response.read(CHUNK_SIZE)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_DOWNLOAD_BYTES:
                            raise RuntimeError(
                                f"source exceeded {MAX_DOWNLOAD_BYTES / 1048576:.0f} MB limit"
                            )
                        output.write(chunk)

            if total == 0:
                raise RuntimeError("source returned an empty response")
            return

        except HTTPError as exc:
            last_error = exc
            if exc.code not in (429, 500, 502, 503, 504):
                raise

            retry_after = exc.headers.get("Retry-After")
            try:
                wait = max(5, int(retry_after)) if retry_after else min(
                    60, 5 * (2 ** attempt)
                )
            except ValueError:
                wait = 10

            print(f"  HTTP {exc.code}; waiting {wait}s...")
            time.sleep(wait)

        except (TimeoutError, URLError) as exc:
            last_error = exc
            wait = min(30, 3 * (2 ** attempt))
            print(f"  Network error; retrying in {wait}s...")
            time.sleep(wait)

    raise RuntimeError(f"source remained unavailable after 5 attempts: {last_error}")


def crop_34(image: Image.Image, crop: dict | None) -> Image.Image:
    width, height = image.size

    zoom = max(1.0, float((crop or {}).get("zoom", 1)))
    x = max(0.0, min(100.0, float((crop or {}).get("x", 50))))
    y = max(0.0, min(100.0, float((crop or {}).get("y", 50))))

    # Match the reviewer's portrait crop geometry:
    # first establish a 3:4 crop at the original scale, then zoom into it.
    base_width = min(width, height * 3 / 4)
    base_height = base_width * 4 / 3

    crop_width = base_width / zoom
    crop_height = base_height / zoom

    max_left = max(0.0, width - crop_width)
    max_top = max(0.0, height - crop_height)

    left = max_left * x / 100
    top = max_top * y / 100

    box = (
        round(left),
        round(top),
        round(left + crop_width),
        round(top + crop_height),
    )

    return image.crop(box)


def process(source: Path, destination: Path, crop: dict | None) -> tuple[int, int]:
    with Image.open(source) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")

        image = crop_34(image, crop)

        image = image.resize(OUTPUT_SIZE, Image.Resampling.LANCZOS)

        destination.parent.mkdir(parents=True, exist_ok=True)
        image.save(
            destination,
            "JPEG",
            quality=88,
            optimize=True,
            progressive=True,
        )

    return OUTPUT_SIZE


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate images even when the destination already exists.",
    )
    args = parser.parse_args()

    approvals = load_json(APPROVALS, {})
    if not approvals:
        # Support the temporary alternate filename if present.
        approvals = load_json(APPROVED_ALT, {})

    players = approvals.get("players", approvals)

    manifest_data = load_json(MANIFEST, {})
    manifest_players = manifest_data.get("players", [])
    manifest_by_id = {p.get("id"): p for p in manifest_players}

    jobs = []

    for player_id, player in players.items():
        if player.get("state") != "approved":
            continue

        candidate, selected_index = selected_candidate(player)
        if not candidate:
            print(f"SKIP {player.get('name', player_id)}: no selected candidate")
            continue

        url = source_url(candidate)
        if not url:
            print(f"SKIP {player.get('name', player_id)}: selected candidate has no URL")
            continue

        crop = crop_for_selected(player, selected_index)
        jobs.append(
            (
                player_id,
                player.get("name", player_id),
                candidate.get("title", ""),
                url,
                crop,
                selected_index,
            )
        )

    # Keep the old manifest as a fallback only for players not present in the
    # approval file. Approved selections always win.
    approved_ids = set(players)
    for player_id, player in manifest_by_id.items():
        if player_id in approved_ids:
            continue
        url = player.get("download_url")
        if url:
            jobs.append(
                (
                    player_id,
                    player.get("name", player_id),
                    "",
                    url,
                    None,
                    None,
                )
            )

    OUT.mkdir(exist_ok=True)

    ok = skipped = failed = 0
    failures = []

    for player_id, name, title, url, crop, selected_index in jobs:
        destination = OUT / f"{player_id}.jpg"

        if destination.exists() and not args.force:
            skipped += 1
            print(f"SKIP {name}: existing {destination.name}")
            continue

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                raw = Path(temp_dir) / "source"
                print(
                    f"DOWN {name}: selected candidate {selected_index} "
                    f"{title or url}"
                )
                download(url, raw)
                width, height = process(raw, destination, crop)

            if (width, height) != OUTPUT_SIZE:
                raise RuntimeError(
                    f"unexpected output dimensions {width}x{height}"
                )

            print(f"OK   {name}: {width}x{height}")
            ok += 1

        except Exception as exc:
            failed += 1
            failures.append((name, str(exc)))
            print(f"FAIL {name}: {exc}")

    print(f"\nProcessed: {ok}; existing: {skipped}; failed: {failed}")

    if failures:
        print("\nFailures:")
        for name, error in failures:
            print(f"- {name}: {error}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
