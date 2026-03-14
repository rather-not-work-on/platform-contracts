#!/usr/bin/env python3

import json
from pathlib import Path
import sys

from jsonschema_compat import load_validator_exports

Draft202012Validator, FormatChecker, _ = load_validator_exports()


CASES = [
    {
        "schema": "c1-run-lifecycle.schema.json",
        "fixture": "c1-run-lifecycle.bad-version.invalid.json",
        "expected_validator": "pattern",
    },
    {
        "schema": "c4-provider-invocation.schema.json",
        "fixture": "c4-provider-invocation.extra-field.invalid.json",
        "expected_validator": "additionalProperties",
    },
    {
        "schema": "c5-observability-event.schema.json",
        "fixture": "c5-observability-event.bad-time.invalid.json",
        "expected_validator": "format",
    },
    {
        "schema": "c8-plan-to-github-projection.schema.json",
        "fixture": "c8-plan-to-github-projection.bad-target-repo.invalid.json",
        "expected_validator": "pattern",
    },
    {
        "schema": "runtime-scheduler-queue-item.schema.json",
        "fixture": "runtime-scheduler-queue-item.bad-state.invalid.json",
        "expected_validator": "enum",
    },
    {
        "schema": "runtime-scheduler-lease-lifecycle.schema.json",
        "fixture": "runtime-scheduler-lease-lifecycle.bad-state.invalid.json",
        "expected_validator": "enum",
    },
    {
        "schema": "runtime-queue-worker-outcome.schema.json",
        "fixture": "runtime-queue-worker-outcome.bad-state.invalid.json",
        "expected_validator": "enum",
    },
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    root = Path(".")
    failures = 0

    for case in CASES:
        schema = load_json(root / "schemas" / case["schema"])
        fixture = load_json(root / "fixtures" / "invalid" / case["fixture"])

        validator = Draft202012Validator(schema, format_checker=FormatChecker())
        errors = list(validator.iter_errors(fixture))
        validators = {e.validator for e in errors}

        if not errors:
            failures += 1
            print(f"[FAIL] {case['fixture']} unexpectedly passed")
            continue

        if case["expected_validator"] not in validators:
            failures += 1
            print(
                f"[FAIL] {case['fixture']} missing expected validator "
                f"{case['expected_validator']} (got: {sorted(validators)})"
            )
            continue

        print(f"[PASS] {case['fixture']} -> {case['expected_validator']}")

    if failures > 0:
        return 1
    print("strict regression checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
