# Ari NBA Cards — Image Review Tool v2

This is a standalone, phone-friendly reviewer for selecting reusable NBA player images for the Ari NBA Cards project.

## Install

Copy these files into the root of the GitHub Pages repository:

- `image-review.html`
- `README_IMAGE_REVIEW.md`

It does **not** replace `players.json`, `image-manifest.json`, `index.html`, the image downloader, or the existing GitHub Actions workflow.

## Open it

After GitHub Pages deploys, open:

`https://icecold-lab.github.io/ari-nba-cards/image-review.html`

Do not open the HTML as `file://` on the phone. It needs to be served by GitHub Pages so that `players.json` can be fetched.

## How it works

- Loads the canonical `players.json`.
- Loads the existing `image-manifest.json` when available.
- Shows only 20 players at a time.
- Searches Wikimedia Commons only for the visible batch.
- Uses Wikimedia's anonymous CORS API (`origin=*`) to retrieve public image metadata and thumbnails.
- Filters out unsupported formats and images smaller than 600px on either dimension.
- Ranks candidates using filename/title relevance, basketball context, dimensions and aspect ratio.
- Caches search results and decisions in browser `localStorage`.
- Uses a controlled request delay and backs off when Wikimedia returns 429/503.

Wikimedia's MediaWiki API explicitly supports anonymous cross-origin requests with `origin=*`, and the Imageinfo module provides image URLs, dimensions, MIME type and metadata. See the official MediaWiki API documentation.

## Review buttons

- **KEEP** — selects that candidate and marks the player approved.
- **MAYBE** — keeps the candidate for comparison without approving it.
- **REJECT** — records that candidate as rejected.
- **Needs better image** — flags the player for another search later.
- **Search again** — clears the cached candidates for that player and searches again.
- **OPEN COMMONS** — opens the Wikimedia Commons file page so the source/licence can be inspected.

## Export / import

Use **Export** to create `image-approvals.json`.

Use **Import** to restore a previously exported review file on another device/browser.

The exported file is deliberately metadata-only. It does not embed image binaries.

## Important licensing note

A Wikimedia Commons search result is not automatically approved for publication merely because it appears in the search. Review the displayed licence/source information and the Commons file page before treating an image as an approved final asset.

## Current scope

This version is deliberately focused on reliable human review. It does not yet modify `image-manifest.json` or download final images. Once the approval workflow has been used and tested, the next step can be a small conversion utility that turns approved selections into the existing image manifest.
