#!/usr/bin/env python3

import argparse
import json
from pathlib import Path
import sys


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate_required(doc: dict, schema: dict):
    errors = []
    for key in schema.get("required", []):
        if key not in doc:
            errors.append(f"missing required key: {key}")
    return errors


def validate_enums(doc: dict, schema: dict, prefix: str = ""):
    errors = []
    props = schema.get("properties", {})
    for key, p in props.items():
        full = f"{prefix}{key}"
        if "enum" in p and key in doc:
            if doc[key] not in p["enum"]:
                errors.append(f"{full} invalid enum '{doc[key]}' not in {p['enum']}")
        if p.get("type") == "object" and key in doc and isinstance(doc[key], dict):
            errors.extend(validate_enums(doc[key], p, prefix=f"{full}."))
    return errors


def validate_pair(schema_path: Path, sample_path: Path):
    schema = load_json(schema_path)
    sample = load_json(sample_path)
    errors = []
    errors.extend(validate_required(sample, schema))
    errors.extend(validate_enums(sample, schema))
    return errors


def main():
    parser = argparse.ArgumentParser(description="Validate C1~C8 contract fixtures")
    parser.add_argument("--root", default=".", help="workspace root containing schemas/ and fixtures/")
    args = parser.parse_args()

    root = Path(args.root)
    pairs = [
        ("c1-run-lifecycle.schema.json", "c1-run-lifecycle.valid.json"),
        ("c2-subtask-handoff.schema.json", "c2-subtask-handoff.valid.json"),
        ("c3-executor-result.schema.json", "c3-executor-result.valid.json"),
        ("c4-provider-invocation.schema.json", "c4-provider-invocation.valid.json"),
        ("c5-observability-event.schema.json", "c5-observability-event.valid.json"),
        ("c6-public-status-projection.schema.json", "c6-public-status-projection.valid.json"),
        ("c7-manual-override-policy.schema.json", "c7-manual-override-policy.valid.json"),
        ("c8-plan-to-github-projection.schema.json", "c8-plan-to-github-projection.valid.json"),
    ]

    failures = 0
    for schema_name, sample_name in pairs:
        schema_path = root / "schemas" / schema_name
        sample_path = root / "fixtures" / sample_name
        errs = validate_pair(schema_path, sample_path)
        if errs:
            failures += 1
            print(f"[FAIL] {schema_name} <- {sample_name}")
            for err in errs:
                print(f"  - {err}")
        else:
            print(f"[PASS] {schema_name} <- {sample_name}")

    if failures > 0:
        return 1
    print("validation passed: all C1~C8 fixtures are valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
