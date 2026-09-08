#!/usr/bin/env python3
"""
Ari's NBA Cards -- Data Validation

Validates players.json (the single canonical data source) and exits
non-zero if anything required is invalid. Run from anywhere:

    python3 update/validate.py [path/to/players.json]

Defaults to ../players.json relative to this script.
"""
import json
import os
import sys

VALID_ABBR = {
    "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET", "GSW",
    "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NOP", "NYK",
    "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SAS", "TOR", "UTA", "WAS",
}
VALID_CATEGORIES = {"Top 150", "All-Time"}
VALID_POSITIONS = {"PG", "SG", "SF", "PF", "C", "PG/SG", "SG/SF", "SF/PF", "PF/C"}
VALID_STATUS = {"active", "retired"}
# draftYear/draftedBy/draftPick/abbr are legitimately optional in this schema
# (pre-existing "dataComplete" convention -- players without verified draft
# info simply omit those keys rather than storing a guessed value).
REQUIRED_FIELDS = [
    "id", "name", "rank", "category", "status", "position",
    "number", "age", "seasons", "awards", "image", "teamName",
    "dataComplete",
]
CURRENT_YEAR = 2026


def fail(errors, msg):
    errors.append(msg)


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "players.json"
    )

    results = {}
    errors = []

    # ---- load & parse ----
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("Ari's NBA Cards \u2014 Data Validation\n")
        print(f"FATAL: could not read/parse {path}: {e}")
        sys.exit(1)

    # ---- exactly 200 players ----
    results["players"] = (len(data) == 200, f"{len(data)}")
    if len(data) != 200:
        fail(errors, f"Expected 200 players, found {len(data)}")

    # ---- malformed records / required fields ----
    malformed = []
    for i, p in enumerate(data):
        if not isinstance(p, dict):
            malformed.append(f"record #{i} is not an object")
            continue
        missing = [f for f in REQUIRED_FIELDS if f not in p]
        if missing:
            malformed.append(f"{p.get('name', f'record #{i}')}: missing field(s) {missing}")
    results["malformed"] = (len(malformed) == 0, malformed)
    if malformed:
        fail(errors, f"{len(malformed)} malformed record(s): " + "; ".join(malformed[:10]))

    names = [p.get("name") for p in data if isinstance(p, dict)]
    ids = [p.get("id") for p in data if isinstance(p, dict)]

    # ---- unique names ----
    dupe_names = sorted({n for n in names if names.count(n) > 1})
    results["unique_names"] = (len(dupe_names) == 0, f"{len(set(names))}")
    if dupe_names:
        fail(errors, f"Duplicate player name(s): {dupe_names}")

    # ---- unique ids ----
    dupe_ids = sorted({i for i in ids if ids.count(i) > 1})
    results["unique_ids"] = (len(dupe_ids) == 0, f"{len(set(ids))}")
    if dupe_ids:
        fail(errors, f"Duplicate id(s): {dupe_ids}")

    # ---- valid categories & ranks ----
    bad_cat = [p["name"] for p in data if p.get("category") not in VALID_CATEGORIES]
    if bad_cat:
        fail(errors, f"Invalid category for: {bad_cat}")

    rank_issues = []
    for cat, expected_count in (("Top 150", 150), ("All-Time", 50)):
        ranks = [p["rank"] for p in data if p.get("category") == cat]
        if len(ranks) != expected_count:
            rank_issues.append(f"{cat} has {len(ranks)} records, expected {expected_count}")
        dupes = sorted({r for r in ranks if ranks.count(r) > 1})
        if dupes:
            rank_issues.append(f"{cat} has duplicate rank(s): {dupes}")
        if sorted(ranks) != list(range(1, expected_count + 1)):
            rank_issues.append(f"{cat} ranks are not a clean 1..{expected_count} sequence")
    results["categories"] = (len(bad_cat) == 0 and len(rank_issues) == 0, rank_issues or bad_cat)
    for msg in rank_issues:
        fail(errors, msg)

    # ---- positions ----
    bad_pos = [p["name"] for p in data if p.get("position") not in VALID_POSITIONS]
    if bad_pos:
        fail(errors, f"Invalid/missing position for: {bad_pos}")

    # ---- status ----
    bad_status = [p["name"] for p in data if p.get("status") not in VALID_STATUS]
    results["status"] = (len(bad_status) == 0, bad_status)
    if bad_status:
        fail(errors, f"Invalid/missing status for: {bad_status}")

    # retired players should not require a current team/jersey; active players should have one
    active_missing_team = [
        p["name"] for p in data
        if p.get("status") == "active" and not p.get("teamName")
    ]
    if active_missing_team:
        fail(errors, f"Active player(s) missing current team: {active_missing_team}")

    # ---- teams / abbreviations ----
    bad_abbr = [
        (p["name"], p.get("abbr")) for p in data
        if p.get("abbr") is not None and p.get("abbr") not in VALID_ABBR
    ]
    results["teams"] = (len(bad_abbr) == 0, bad_abbr)
    if bad_abbr:
        fail(errors, f"Invalid team abbreviation(s): {bad_abbr}")

    # abbr/teamName presence should agree
    mismatched = [
        p["name"] for p in data
        if bool(p.get("abbr")) != bool(p.get("teamName"))
    ]
    if mismatched:
        fail(errors, f"abbr/teamName presence mismatch for: {mismatched}")

    # ---- jersey numbers are strings ----
    bad_number_type = [
        p["name"] for p in data
        if p.get("number") is not None and not isinstance(p.get("number"), str)
    ]
    results["jersey_numbers"] = (len(bad_number_type) == 0, bad_number_type)
    if bad_number_type:
        fail(errors, f"Jersey number(s) not stored as string: {bad_number_type}")

    # no two players on the same current team may share a jersey number
    from collections import defaultdict
    by_team = defaultdict(list)
    for p in data:
        if p.get("teamName") and p.get("number"):
            by_team[p["teamName"]].append((p["number"], p["name"]))
    number_conflicts = []
    for team, players in by_team.items():
        nums = [n for n, _ in players]
        dupes = {n for n in nums if nums.count(n) > 1}
        if dupes:
            number_conflicts.append((team, [nm for n, nm in players if n in dupes]))
    if number_conflicts:
        fail(errors, f"Duplicate jersey numbers within a team: {number_conflicts}")

    # ---- draft data sanity ----
    draft_issues = []
    for p in data:
        dy = p.get("draftYear")
        dp = p.get("draftPick")
        if dy is not None and (dy > CURRENT_YEAR or dy < 1946):
            draft_issues.append(f"{p['name']}: implausible draftYear {dy}")
        if dp is not None and dy is None:
            draft_issues.append(f"{p['name']}: has draftPick but no draftYear")
        if dy == CURRENT_YEAR and p.get("seasons") != 0:
            draft_issues.append(f"{p['name']}: drafted {CURRENT_YEAR} but seasons={p.get('seasons')} (expected 0)")
    results["draft_data"] = (len(draft_issues) == 0, draft_issues)
    for msg in draft_issues:
        fail(errors, msg)

    # ---- award counts non-negative ----
    award_issues = []
    for p in data:
        a = p.get("awards") or {}
        for k, v in a.items():
            if v is not None and v < 0:
                award_issues.append(f"{p['name']}: negative {k} ({v})")
    results["awards"] = (len(award_issues) == 0, award_issues)
    for msg in award_issues:
        fail(errors, msg)

    # ---- print report ----
    print("Ari's NBA Cards \u2014 Data Validation\n")

    def line(label, ok, detail):
        status = "PASS" if ok else "FAIL"
        print(f"{label:<15}{status} \u2014 {detail}")

    line("Players:", results["players"][0], results["players"][1])
    line("Unique names:", results["unique_names"][0], results["unique_names"][1])
    line("Unique IDs:", results["unique_ids"][0], results["unique_ids"][1])
    line("Categories:", results["categories"][0], "OK" if results["categories"][0] else results["categories"][1])
    line("Teams:", results["teams"][0], "OK" if results["teams"][0] else results["teams"][1])
    line("Jersey numbers:", results["jersey_numbers"][0], "OK" if results["jersey_numbers"][0] else results["jersey_numbers"][1])
    line("Draft data:", results["draft_data"][0], "OK" if results["draft_data"][0] else results["draft_data"][1])
    line("Awards:", results["awards"][0], "OK" if results["awards"][0] else results["awards"][1])
    line("Status:", results["status"][0], "OK" if results["status"][0] else results["status"][1])
    line("Malformed:", results["malformed"][0], "0" if results["malformed"][0] else results["malformed"][1])

    print()
    if errors:
        print("RESULT: FAIL\n")
        print("Details:")
        for e in errors:
            print(" -", e)
        sys.exit(1)
    else:
        print("RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
