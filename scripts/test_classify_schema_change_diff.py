#!/usr/bin/env python3

import json
from pathlib import Path
import subprocess
import sys
import tempfile


def fail(message: str):
    print(f"[FAIL] {message}")
    return 1


def main():
    root = Path(".")
    with tempfile.TemporaryDirectory() as td:
        report_path = Path(td) / "semver-report.json"
        cmd = [
            sys.executable,
            "scripts/classify_schema_change.py",
            "--enforce-expected",
            "--report",
            str(report_path),
        ]
        proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr)
            return fail("classification command failed")

        if not report_path.exists():
            return fail("report not generated")

        report = json.loads(report_path.read_text(encoding="utf-8"))
        results = report.get("results", [])
        if not results:
            return fail("no scenario results found")

        for item in results:
            expected = item.get("expected_bump")
            computed = item.get("computed_bump")
            if expected is None:
                return fail(f"expected_bump missing for {item.get('id')}")
            if expected != computed:
                return fail(f"bump mismatch for {item.get('id')}: expected={expected} computed={computed}")

            rationale = item.get("rationale")
            if not isinstance(rationale, list):
                return fail(f"rationale missing list type for {item.get('id')}")
            for change in rationale:
                if not change.get("path"):
                    return fail(f"rationale missing path for {item.get('id')}")
                if not change.get("change_type"):
                    return fail(f"rationale missing change_type for {item.get('id')}")
                if change.get("severity") not in {"patch", "minor", "major"}:
                    return fail(f"invalid severity for {item.get('id')}")

            if expected in {"minor", "major"} and len(rationale) == 0:
                return fail(f"empty rationale for semantic bump in {item.get('id')}")

    print("schema diff semver regression checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
