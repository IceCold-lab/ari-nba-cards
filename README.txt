Ari's NBA Cards v9 -- Engineering / Data-Hardening Release

This is an engineering and data-integrity pass. The 200-player list, ranks,
categories, visual design, card layout, scoring system, and Learn/Guess/
Shuffle behaviour are all UNCHANGED from v8. No images were chosen,
downloaded, cropped, edited, or replaced in this release.

WHAT CHANGED IN V9
-------------------
1. Full data-integrity audit of all 200 records (see "Audit results" below).

2. Jersey numbers are now strings, not numbers (e.g. "00" instead of 0),
   so leading zeroes are preserved. The UI renders correctly whether a
   number is already zero-padded ("00") or not ("8" -> displays as "08").

3. Retired-player data model: every record now has a "status" field,
   "active" or "retired". Retired players are not forced to carry a
   current team/jersey -- the card shows "Retired" in place of a
   team/jersey combination for them. This is a status, not a new
   category; the two existing categories (Top 150 / All-Time 50) are
   unchanged.

4. players.json is now the single source of truth. index.html no longer
   embeds a second, manually-maintained copy of the 200 player records --
   it fetches players.json at load time. (Practical consequence: the app
   must be served over http/https -- e.g. GitHub Pages, or any local dev
   server -- rather than opened directly as a file:// URL, since browsers
   generally block fetch() of local files under file://. This is a
   necessary trade-off of removing the duplicated data, called out here
   per the "no silent guessing" instruction rather than left undocumented.)

5. Created update/validate.py, a standalone validation script. Run it with:
       python3 update/validate.py
   It exits non-zero and lists the specific player(s)/field(s) affected
   if anything required is invalid.

6. Image metadata schema (foundation only -- not populated with real
   assets, nothing downloaded or chosen):
       "image": { "file": "images/<player-id>.jpg", "source": "", "era": "current" | "prime" }
   "era" is "current" for active players and "prime" for retired players.
   This field is NOT yet wired into the UI -- the app's actual photo
   lookup (live Wikipedia thumbnail fetch by player name) is unchanged
   from v8, per instructions not to touch image selection/behaviour.

7. Image-loading robustness hardening (bug fixes, not a redesign):
   - The photo fetch and its response parsing are wrapped so a network
     failure, bad JSON, or missing thumbnail can never throw an uncaught
     error or block card rendering/navigation.
   - Added an onerror handler to the loaded <img> itself, so a broken or
     expired image URL now falls back to the placeholder icon instead of
     showing a broken-image glyph (previously it did not fall back).

8. Optional debug/validation mode: append ?debug=1 to the URL to show a
   small fixed diagnostic panel (players loaded, valid records, duplicate
   ids/names, image-manifest presence). It does nothing and adds nothing
   to the page unless that query parameter is present.

9. Every player record also gained a unique "id" (a stable kebab-case
   slug of their name, e.g. "nikola-jokic"), used for the id/name
   uniqueness checks and as the planned image filename stem.

AUDIT RESULTS
-------------
Structural checks across all 200 records: exactly 200 records, 200 unique
names/ids, unique ranks within each category (1-150 and 1-50, no gaps or
duplicates), all categories valid, all team abbreviations valid, no
malformed records, no negative award counts, all 2026 draftees correctly
show seasons: 0.

Corrections made (all independently verified against current reporting
before changing anything):
 - Jordan Clarkson (Knicks): jersey number corrected to "00" (per explicit
   instruction).
 - Fixed 7 additional jersey-number errors, all involving two teammates
   in this dataset sharing the same number (impossible in the real NBA) --
   in each case one player's number was wrong:
     AJ Dybantsa (Wizards): 3 -> 4 (Trae Young already wears 3)
     Anthony Davis (Wizards): 3 -> 23
     Darryn Peterson (Jazz): 3 -> 22 (Keyonte George already wears 3)
     Donovan Clingan (Trail Blazers): 33 -> 23 (Toumani Camara wears 33)
     Kel'el Ware (Bucks): 7 -> 9 (Kevin Porter Jr. already wears 7)
     Cameron Boozer (Grizzlies): 2 -> 27 (Ty Jerome already wears 2)
     Caleb Wilson (Bulls): 100 -> 8 (100 is not a valid NBA jersey number)
 - "status" (active/retired) was derived for all 200 records directly
   from the existing teamName field (blank teamName = retired, a
   convention the data already used consistently) -- no new judgment
   calls were made about any individual player's real-world status.

Values that could NOT be confidently verified or corrected (left
unchanged, flagged here rather than guessed):
 - For long-retired/deceased All-Time legends, the "age" and "seasons"
   fields appear to follow a "years since draft, as if still living today"
   convention rather than real career length or age at retirement/death
   (e.g. several deceased players show a hypothetical current age, and
   "seasons" values far exceed any real NBA career). This is a pre-existing
   design choice from earlier versions, not something introduced or
   verified in this pass. Changing it would require redefining what those
   fields mean for retired players, which was out of scope ("don't
   arbitrarily change data because another value seems preferable") --
   flagged here for a future decision rather than silently altered.
 - A full field-by-field re-verification of all 159 active players' current
   team/number/age against live sources was not exhaustively performed in
   this pass beyond the specific conflicts the audit surfaced (the 8 jersey
   numbers above) and the 9 replacement All-Time players (already verified
   in v8). Given the volume (159 players) this would require, only the
   objectively-detectable structural issues (impossible duplicate jersey
   numbers within a team, out-of-range numbers) were used to target
   verification, rather than spot-checking players at random.

VALIDATION RESULTS (this build)
--------------------------------
$ python3 update/validate.py

Ari's NBA Cards -- Data Validation

Players:       PASS -- 200
Unique names:  PASS -- 200
Unique IDs:    PASS -- 200
Categories:    PASS -- OK
Teams:         PASS -- OK
Jersey numbers:PASS -- OK
Draft data:    PASS -- OK
Awards:        PASS -- OK
Status:        PASS -- OK
Malformed:     PASS -- 0

RESULT: PASS

Also verified before packaging:
 - players.json parses as valid JSON; the app's JS passes `node --check`.
 - Simulated all 11 functional checks (data loads; all 200 cards can be
   paged through in both directions with clean wraparound; Top 150 /
   All-Time / All filters return exactly 150 / 50 / 200 cards; Learn and
   Guess modes correctly show/hide the name; Shuffle reorders the full
   200-card deck; streak increments on "Got it!" and resets on "Didn't
   know"; a retired player's card shows "Retired" instead of a team;
   Jordan Clarkson's card shows "#00"; no records were lost or
   duplicated; repeated photo-fetch failures never throw an unhandled
   error or block navigation) -- all passed, including under strict
   unhandled-exception/unhandled-rejection monitoring.

WHAT WAS DELIBERATELY NOT CHANGED
----------------------------------
 - The 200-player list, rankings, and Top 150 / All-Time 50 categories.
 - Visual design, card layout, and CSS (aside from the small "Retired"
   label and the hidden debug panel, which is invisible without ?debug=1).
 - Scoring/streak system, Learn/Guess behaviour, Shuffle behaviour.
 - Player images: no image was chosen, downloaded, cropped, edited, or
   replaced. The live Wikipedia-thumbnail photo lookup behaves exactly as
   it did in v8; only its error-handling was hardened.
 - Any jersey number, age, draft field, or award not specifically flagged
   above as independently verified and corrected.
