#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


SEVERITY_ORDER = {"patch": 0, "minor": 1, "major": 2}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def bump_for_change(change: dict):
    change_type = change.get("type")
    if change_type in {"required_removed", "required_renamed", "enum_semantics_changed"}:
        return "major"
    if change_type in {"optional_added", "enum_value_added_with_fallback"}:
        return "minor"
    return "patch"


def max_bump(changes):
    current = "patch"
    for c in changes:
        candidate = bump_for_change(c)
        if SEVERITY_ORDER[candidate] > SEVERITY_ORDER[current]:
            current = candidate
    return current


def main():
    parser = argparse.ArgumentParser(description="Classify schema change impact as major/minor/patch")
    parser.add_argument(
        "--input",
        default="compatibility/fixtures/schema-change-scenarios.json",
        help="Path to schema change scenarios",
    )
    parser.add_argument(
        "--output-dir",
        default="compatibility/reports",
        help="Directory where classification report is written",
    )
    parser.add_argument(
        "--enforce-expected",
        action="store_true",
        help="Fail when computed bump differs from expected_bump in scenarios",
    )
    args = parser.parse_args()

    doc = load_json(Path(args.input))
    scenarios = doc.get("scenarios", [])
    results = []
    mismatch_count = 0

    for sc in scenarios:
        computed = max_bump(sc.get("changes", []))
        expected = sc.get("expected_bump", "patch")
        ok = computed == expected
        if not ok:
            mismatch_count += 1
        results.append(
            {
                "scenario_id": sc.get("id"),
                "description": sc.get("description"),
                "expected_bump": expected,
                "computed_bump": computed,
                "ok": ok,
            }
        )

    now = datetime.now(timezone.utc)
    report = {
        "generated_at_utc": now.isoformat(),
        "input": args.input,
        "scenario_count": len(results),
        "mismatch_count": mismatch_count,
        "results": results,
    }

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"semver-classification-{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")

    print(f"report written: {out_path}")
    print(f"scenario_count={len(results)} mismatch_count={mismatch_count}")

    if args.enforce_expected and mismatch_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
