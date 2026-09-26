# Ari NBA Cards — 2026 image/data integration package

This package is prepared against the current repository architecture.

Files:
- `approved-images.json`: 126 approved image selections extracted from the completed review approval file, with saved crop parameters.
- `roster-overrides.json`: current transaction/team/number corrections verified against NBA.com current team pages and the 2026 offseason transaction tracker.
- `fetch_images.py`: replacement downloader that consumes approved images and applies the saved 3:4 crop in Pillow.
- `ui-integration-patch.js`: narrow UI patch for the portrait frame and Learn-mode reveal behavior.

## Important
The connected GitHub integration is currently returning HTTP 403 for repository writes, so these files could not be committed directly.

The existing `index.html` must load `ui-integration-patch.js` after its main script (or the equivalent small changes can be merged into the existing script). Do not replace the existing application architecture.

## Data changes verified
NBA.com transaction tracker and current team pages were used to verify the 2026 offseason moves affecting the card set, including:
- Kawhi Leonard -> Toronto; Brandon Ingram -> LA Clippers.
- Giannis Antetokounmpo and Bobby Portis -> Miami.
- Jaylen Brown -> Philadelphia; Paul George -> Boston.
- LaMelo Ball -> Minnesota; Naz Reid -> Charlotte; Josh Green -> Utah; Nic Claxton -> Chicago.
- Miles Bridges -> Phoenix; Grayson Allen and Royce O'Neale -> Charlotte.
- Ja Morant -> Portland; Jerami Grant and Kris Murray -> Memphis.
- Dorian Finney-Smith -> Atlanta; plus earlier Atlanta/Hornets/Mavericks/Thunder moves where the player is in the card data.
- D'Angelo Russell was subsequently waived by Memphis on 2026-09-25 and should be treated as a free agent unless he signs elsewhere.

Do not infer a final team from a trade announcement if a later transaction supersedes it; the current team pages should win.

## Learn mode
Before reveal, Learn mode should show the player's name only. Image, team, number, facts, draft data and accomplishments are hidden until Reveal.

## Build
The image output is normalized to exactly 900x1200 JPEG (3:4) and the crop is applied before resizing.
