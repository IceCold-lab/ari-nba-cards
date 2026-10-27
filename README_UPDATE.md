# Ari’s NBA Cards — representation + compact biography update

## Files
- `index.html`: app HTML with the biography displayed as one compact line, using a flag for birthplace and adding `(represents 🇺🇸 United States)` only when a known representation differs from birthplace.
- `players.json`: 200 player records with `representedCountry` and `representedCountryCode` keys on every record.

## Install on GitHub
1. Open the `IceCold-lab/ari-nba-cards` repository on GitHub.
2. Open `players.json` → pencil/Edit → replace the full contents with the supplied `players.json` file → Commit changes.
3. Open `index.html` → pencil/Edit → replace the full contents with the supplied `index.html` file → Commit changes.
4. Use two separate commits if GitHub's mobile editor makes replacing both files easier.
5. Reload the published site. If the old version persists, open it in an incognito tab or clear site data/cache.

## Data handling
Both representation fields exist on all 200 records. Known senior international representation is populated where reasonably established; uncertain/unverified cases remain `null`. A player's birthplace, citizenship, ancestry, or eligibility is not by itself treated as proof of the country they represent. This is a conservative starter pass, not a fully sourced national-team audit of every player.

## Expected examples
- Josh Giddey: `🇦🇺 Melbourne, Victoria`
- Joel Embiid: `🇨🇲 Yaoundé (represents 🇺🇸 United States)`
- Sandro Mamukelashvili: `🇺🇸 New York City (represents 🇬🇪 Georgia)`

The source data's existing birthplace and death-date values are retained; this update only adds/normalises representation fields and changes the biography display.
