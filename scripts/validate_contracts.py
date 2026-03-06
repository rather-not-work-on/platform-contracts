#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
import sys
from typing import Dict, List, Tuple

try:
    from jsonschema import Draft202012Validator, FormatChecker
    from jsonschema.exceptions import SchemaError
except ImportError:
    print(
        "[ERR] missing dependency: jsonschema\n"
        "      install with: python3 -m pip install -r requirements-dev.txt",
        file=sys.stderr,
    )
    sys.exit(2)

REQUIRED_FORMAT_CHECKERS = {"date-time"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def build_pairs(root: Path) -> Tuple[List[Tuple[Path, Path]], List[str]]:
    schemas_dir = root / "schemas"
    fixtures_dir = root / "fixtures"

    pairs: List[Tuple[Path, Path]] = []
    errors: List[str] = []

    schema_paths = []
    for candidate in sorted(schemas_dir.glob("*.schema.json")):
        if candidate.name.startswith("._") or candidate.name == ".DS_Store":
            continue
        schema_paths.append(candidate)
    if not schema_paths:
        errors.append(f"no schema files found under {schemas_dir}")
        return pairs, errors

    for schema_path in schema_paths:
        fixture_name = schema_path.name.replace(".schema.json", ".valid.json")
        fixture_path = fixtures_dir / fixture_name
        if not fixture_path.exists():
            errors.append(f"missing fixture for {schema_path.name}: expected {fixture_path}")
            continue
        pairs.append((schema_path, fixture_path))

    return pairs, errors


def format_path(path_tokens):
    if not path_tokens:
        return "$"
    parts = []
    for token in path_tokens:
        if isinstance(token, int):
            parts.append(f"[{token}]")
        else:
            parts.append(f".{token}")
    return "$" + "".join(parts)


def validate_pair(schema_path: Path, sample_path: Path):
    schema = load_json(schema_path)
    sample = load_json(sample_path)

    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    formatted_errors = []
    for error in sorted(validator.iter_errors(sample), key=lambda e: list(e.path)):
        path = format_path(error.absolute_path)
        formatted_errors.append(
            {
                "path": path,
                "message": error.message,
                "validator": error.validator,
            }
        )
    return formatted_errors


def main():
    parser = argparse.ArgumentParser(description="Validate C1~C8 contract fixtures with JSON Schema Draft 2020-12")
    parser.add_argument("--root", default=".", help="workspace root containing schemas/ and fixtures/")
    parser.add_argument(
        "--report",
        default="compatibility/reports/latest-validation-report.json",
        help="JSON report output path",
    )
    args = parser.parse_args()

    root = Path(args.root)
    format_checker = FormatChecker()
    missing_checkers = sorted(REQUIRED_FORMAT_CHECKERS - set(format_checker.checkers.keys()))
    if missing_checkers:
        print(
            "[ERR] missing format checkers: "
            + ", ".join(missing_checkers)
            + "\n      install with: python3 -m pip install -r requirements-dev.txt",
            file=sys.stderr,
        )
        return 2

    report_path = Path(args.report)
    if not report_path.is_absolute():
        report_path = root / report_path

    pairs, pair_errors = build_pairs(root)
    results: List[Dict] = []
    failures = 0

    if pair_errors:
        for err in pair_errors:
            print(f"[FAIL] {err}")
        failures += len(pair_errors)

    for schema_path, sample_path in pairs:
        try:
            errors = validate_pair(schema_path, sample_path)
        except SchemaError as exc:
            failures += 1
            print(f"[FAIL] {schema_path.name} schema invalid")
            print(f"  - {exc.message}")
            results.append(
                {
                    "schema": str(schema_path),
                    "fixture": str(sample_path),
                    "verdict": "fail",
                    "errors": [{"path": "$schema", "message": exc.message, "validator": "schema"}],
                }
            )
            continue

        if errors:
            failures += 1
            print(f"[FAIL] {schema_path.name} <- {sample_path.name}")
            for err in errors:
                print(f"  - {err['path']}: {err['message']} ({err['validator']})")
            results.append(
                {
                    "schema": str(schema_path),
                    "fixture": str(sample_path),
                    "verdict": "fail",
                    "errors": errors,
                }
            )
            continue

        print(f"[PASS] {schema_path.name} <- {sample_path.name}")
        results.append(
            {
                "schema": str(schema_path),
                "fixture": str(sample_path),
                "verdict": "pass",
                "errors": [],
            }
        )

    report = {
        "root": str(root.resolve()),
        "pair_count": len(pairs),
        "failure_count": failures,
        "verdict": "pass" if failures == 0 else "fail",
        "results": results,
    }

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    print(f"report written: {report_path}")

    if failures > 0:
        return 1
    print("validation passed: all C1~C8 fixtures satisfy JSON Schema validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
