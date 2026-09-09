#!/usr/bin/env python3
"""
Ari's NBA Cards -- Data Validation

Validates players.json (the single canonical data source) and exits
non-zero if anything required is invalid.

Run:
    python3 validate.py [path/to/players.json]

Defaults to players.json in the repository root.
"""

import json
import os
import sys
from collections import defaultdict


VALID_ABBR = {
    "ATL", "BOS", "BKN", "CHA", "CHI", "CLE", "DAL", "DEN", "DET", "GSW",
    "HOU", "IND", "LAC", "LAL", "MEM", "MIA", "MIL", "MIN", "NOP", "NYK",
    "OKC", "ORL", "PHI", "PHX", "POR", "SAC", "SAS", "TOR", "UTA", "WAS",
}

VALID_CATEGORIES = {
    "Current Players",
    "Classic Players",
}

VALID_POSITIONS = {
    "PG", "SG", "SF", "PF", "C",
    "PG/SG", "SG/SF", "SF/PF", "PF/C",
}

VALID_STATUS = {
    "active",
    "retired",
}

REQUIRED_FIELDS = [
    "id",
    "name",
    "rank",
    "category",
    "status",
    "position",
    "number",
    "age",
    "seasons",
    "awards",
    "image",
    "teamName",
    "dataComplete",
]

CURRENT_YEAR = 2026


def fail(errors, msg):
    errors.append(msg)


def main():
    # ------------------------------------------------------------
    # Locate players.json
    # ------------------------------------------------------------

    if len(sys.argv) > 1:
        path = sys.argv[1]
    else:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(script_dir, "players.json")

        # Fallback for the older update/validate.py layout
        if not os.path.exists(path):
            path = os.path.join(script_dir, "..", "players.json")

    results = {}
    errors = []

    # ------------------------------------------------------------
    # Load JSON
    # ------------------------------------------------------------

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print("Ari's NBA Cards — Data Validation\n")
        print(f"FATAL: could not read/parse {path}: {e}")
        sys.exit(1)

    if not isinstance(data, list):
        print("Ari's NBA Cards — Data Validation\n")
        print("FATAL: players.json must contain a JSON array")
        sys.exit(1)

    # ------------------------------------------------------------
    # Exactly 200 players
    # ------------------------------------------------------------

    results["players"] = (
        len(data) == 200,
        f"{len(data)}"
    )

    if len(data) != 200:
        fail(
            errors,
            f"Expected 200 players, found {len(data)}"
        )

    # ------------------------------------------------------------
    # Malformed records / required fields
    # ------------------------------------------------------------

    malformed = []

    for i, p in enumerate(data):
        if not isinstance(p, dict):
            malformed.append(
                f"record #{i} is not an object"
            )
            continue

        missing = [
            field
            for field in REQUIRED_FIELDS
            if field not in p
        ]

        if missing:
            malformed.append(
                f"{p.get('name', f'record #{i}')}: "
                f"missing field(s) {missing}"
            )

    results["malformed"] = (
        len(malformed) == 0,
        malformed
    )

    if malformed:
        fail(
            errors,
            f"{len(malformed)} malformed record(s): "
            + "; ".join(malformed[:10])
        )

    # ------------------------------------------------------------
    # Names and IDs
    # ------------------------------------------------------------

    names = [
        p.get("name")
        for p in data
        if isinstance(p, dict)
    ]

    ids = [
        p.get("id")
        for p in data
        if isinstance(p, dict)
    ]

    # Unique names

    dupe_names = sorted({
        n for n in names
        if names.count(n) > 1
    })

    results["unique_names"] = (
        len(dupe_names) == 0,
        f"{len(set(names))}"
    )

    if dupe_names:
        fail(
            errors,
            f"Duplicate player name(s): {dupe_names}"
        )

    # Unique IDs

    dupe_ids = sorted({
        i for i in ids
        if ids.count(i) > 1
    })

    results["unique_ids"] = (
        len(dupe_ids) == 0,
        f"{len(set(ids))}"
    )

    if dupe_ids:
        fail(
            errors,
            f"Duplicate id(s): {dupe_ids}"
        )

    # ------------------------------------------------------------
    # Categories and ranks
    #
    # Current Players = active
    # Classic Players = retired
    #
    # Each category must have sequential ranks beginning at 1.
    # ------------------------------------------------------------

    bad_cat = [
        p["name"]
        for p in data
        if p.get("category") not in VALID_CATEGORIES
    ]

    if bad_cat:
        fail(
            errors,
            f"Invalid category for: {bad_cat}"
        )

    rank_issues = []

    category_rules = (
        ("Current Players", "active"),
        ("Classic Players", "retired"),
    )

    for category, expected_status in category_rules:

        members = [
            p for p in data
            if p.get("category") == category
        ]

        ranks = [
            p.get("rank")
            for p in members
            if isinstance(p.get("rank"), int)
        ]

        expected_count = sum(
            1
            for p in data
            if p.get("status") == expected_status
        )

        # Correct number of players

        if len(members) != expected_count:
            rank_issues.append(
                f"{category} has {len(members)} records, "
                f"expected {expected_count}"
            )

        # All ranks must be integers

        non_integer_ranks = [
            p["name"]
            for p in members
            if not isinstance(p.get("rank"), int)
        ]

        if non_integer_ranks:
            rank_issues.append(
                f"{category} has non-integer rank(s): "
                f"{non_integer_ranks}"
            )

        # No duplicate ranks

        dupes = sorted({
            r for r in ranks
            if ranks.count(r) > 1
        })

        if dupes:
            rank_issues.append(
                f"{category} has duplicate rank(s): {dupes}"
            )

        # Ranks must be 1..N

        expected_ranks = list(
            range(1, expected_count + 1)
        )

        if sorted(ranks) != expected_ranks:
            rank_issues.append(
                f"{category} ranks are not a clean "
                f"1..{expected_count} sequence"
            )

        # Category must agree with player status

        mismatched_status = [
            p["name"]
            for p in members
            if p.get("status") != expected_status
        ]

        if mismatched_status:
            rank_issues.append(
                f"{category} has player(s) with wrong status: "
                f"{mismatched_status}"
            )

    results["categories"] = (
        len(bad_cat) == 0 and len(rank_issues) == 0,
        rank_issues if rank_issues else bad_cat
    )

    for msg in rank_issues:
        fail(errors, msg)

    # ------------------------------------------------------------
    # Positions
    # ------------------------------------------------------------

    bad_pos = [
        p["name"]
        for p in data
        if p.get("position") not in VALID_POSITIONS
    ]

    results["positions"] = (
        len(bad_pos) == 0,
        bad_pos
    )

    if bad_pos:
        fail(
            errors,
            f"Invalid/missing position for: {bad_pos}"
        )

    # ------------------------------------------------------------
    # Status
    # ------------------------------------------------------------

    bad_status = [
        p["name"]
        for p in data
        if p.get("status") not in VALID_STATUS
    ]

    results["status"] = (
        len(bad_status) == 0,
        bad_status
    )

    if bad_status:
        fail(
            errors,
            f"Invalid/missing status for: {bad_status}"
        )

    # ------------------------------------------------------------
    # Active players need a current team
    # ------------------------------------------------------------

    active_missing_team = [
        p["name"]
        for p in data
        if p.get("status") == "active"
        and not p.get("teamName")
    ]

    if active_missing_team:
        fail(
            errors,
            f"Active player(s) missing current team: "
            f"{active_missing_team}"
        )

    # ------------------------------------------------------------
    # Teams / abbreviations
    # ------------------------------------------------------------

    bad_abbr = [
        (p["name"], p.get("abbr"))
        for p in data
        if p.get("abbr") is not None
        and p.get("abbr") not in VALID_ABBR
    ]

    results["teams"] = (
        len(bad_abbr) == 0,
        bad_abbr
    )

    if bad_abbr:
        fail(
            errors,
            f"Invalid team abbreviation(s): {bad_abbr}"
        )

    # abbr and teamName should either both exist or both be absent

    mismatched_team_fields = [
        p["name"]
        for p in data
        if bool(p.get("abbr")) != bool(p.get("teamName"))
    ]

    if mismatched_team_fields:
        fail(
            errors,
            "abbr/teamName presence mismatch for: "
            f"{mismatched_team_fields}"
        )

    # ------------------------------------------------------------
    # Jersey numbers
    # ------------------------------------------------------------

    bad_number_type = [
        p["name"]
        for p in data
        if p.get("number") is not None
        and not isinstance(p.get("number"), str)
    ]

    results["jersey_numbers"] = (
        len(bad_number_type) == 0,
        bad_number_type
    )

    if bad_number_type:
        fail(
            errors,
            "Jersey number(s) not stored as string: "
            f"{bad_number_type}"
        )

    # No two players on the same current team may share a number

    by_team = defaultdict(list)

    for p in data:
        if p.get("teamName") and p.get("number"):
            by_team[p["teamName"]].append(
                (p["number"], p["name"])
            )

    number_conflicts = []

    for team, players in by_team.items():

        nums = [
            number
            for number, _ in players
        ]

        dupes = {
            number
            for number in nums
            if nums.count(number) > 1
        }

        if dupes:
            number_conflicts.append(
                (
                    team,
                    [
                        name
                        for number, name in players
                        if number in dupes
                    ]
                )
            )

    if number_conflicts:
        fail(
            errors,
            "Duplicate jersey numbers within a team: "
            f"{number_conflicts}"
        )

    # ------------------------------------------------------------
    # Draft data sanity
    # ------------------------------------------------------------

    draft_issues = []

    for p in data:

        dy = p.get("draftYear")
        dp = p.get("draftPick")

        if dy is not None:

            if not isinstance(dy, int):
                draft_issues.append(
                    f"{p['name']}: draftYear is not an integer"
                )

            elif dy > CURRENT_YEAR or dy < 1946:
                draft_issues.append(
                    f"{p['name']}: implausible draftYear {dy}"
                )

        if dp is not None and dy is None:
            draft_issues.append(
                f"{p['name']}: has draftPick but no draftYear"
            )

        if (
            dy == CURRENT_YEAR
            and p.get("seasons") != 0
        ):
            draft_issues.append(
                f"{p['name']}: drafted {CURRENT_YEAR} "
                f"but seasons={p.get('seasons')} "
                f"(expected 0)"
            )

    results["draft_data"] = (
        len(draft_issues) == 0,
        draft_issues
    )

    for msg in draft_issues:
        fail(errors, msg)

    # ------------------------------------------------------------
    # Award counts must be non-negative
    # ------------------------------------------------------------

    award_issues = []

    for p in data:

        awards = p.get("awards") or {}

        if not isinstance(awards, dict):
            award_issues.append(
                f"{p['name']}: awards is not an object"
            )
            continue

        for key, value in awards.items():

            if value is not None:

                if not isinstance(value, int):
                    award_issues.append(
                        f"{p['name']}: {key} is not an integer"
                    )

                elif value < 0:
                    award_issues.append(
                        f"{p['name']}: negative {key} ({value})"
                    )

    results["awards"] = (
        len(award_issues) == 0,
        award_issues
    )

    for msg in award_issues:
        fail(errors, msg)

    # ------------------------------------------------------------
    # Print report
    # ------------------------------------------------------------

    print("Ari's NBA Cards — Data Validation\n")

    def line(label, ok, detail):
        status = "PASS" if ok else "FAIL"
        print(
            f"{label:<15}{status} — {detail}"
        )

    line(
        "Players:",
        results["players"][0],
        results["players"][1]
    )

    line(
        "Unique names:",
        results["unique_names"][0],
        results["unique_names"][1]
    )

    line(
        "Unique IDs:",
        results["unique_ids"][0],
        results["unique_ids"][1]
    )

    line(
        "Categories:",
        results["categories"][0],
        "OK"
        if results["categories"][0]
        else results["categories"][1]
    )

    line(
        "Teams:",
        results["teams"][0],
        "OK"
        if results["teams"][0]
        else results["teams"][1]
    )

    line(
        "Jersey numbers:",
        results["jersey_numbers"][0],
        "OK"
        if results["jersey_numbers"][0]
        else results["jersey_numbers"][1]
    )

    line(
        "Draft data:",
        results["draft_data"][0],
        "OK"
        if results["draft_data"][0]
        else results["draft_data"][1]
    )

    line(
        "Awards:",
        results["awards"][0],
        "OK"
        if results["awards"][0]
        else results["awards"][1]
    )

    line(
        "Status:",
        results["status"][0],
        "OK"
        if results["status"][0]
        else results["status"][1]
    )

    line(
        "Malformed:",
        results["malformed"][0],
        "0"
        if results["malformed"][0]
        else results["malformed"][1]
    )

    print()

    if errors:

        print("RESULT: FAIL\n")
        print("Details:")

        for error in errors:
            print(" -", error)

        sys.exit(1)

    else:

        print("RESULT: PASS")
        sys.exit(0)


if __name__ == "__main__":
    main()
