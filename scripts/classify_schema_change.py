#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


SEVERITY_ORDER = {"patch": 0, "minor": 1, "major": 2}
DOC_ONLY_KEYS = {"title", "description", "examples", "$comment", "default"}
IGNORED_KEYS = {"$schema", "$id"}
METADATA_FILENAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def is_metadata_path(path: Path):
    return path.name.startswith("._") or path.name in METADATA_FILENAMES


def pointer(base: str, key: str):
    escaped = key.replace("~", "~0").replace("/", "~1")
    if base == "#":
        return f"#/{escaped}"
    return f"{base}/{escaped}"


def add_change(changes, severity: str, change_type: str, path: str, detail: str):
    changes.append(
        {
            "severity": severity,
            "change_type": change_type,
            "path": path,
            "detail": detail,
        }
    )


def normalize_types(raw):
    if raw is None:
        return set()
    if isinstance(raw, list):
        return {str(item) for item in raw}
    return {str(raw)}


def compare_bounds(changes, before, after, path: str):
    rules = [
        ("minLength", True),
        ("minimum", True),
        ("exclusiveMinimum", True),
        ("minItems", True),
        ("maxLength", False),
        ("maximum", False),
        ("exclusiveMaximum", False),
        ("maxItems", False),
    ]

    for key, larger_is_stricter in rules:
        if key not in before or key not in after:
            continue
        old_value = before[key]
        new_value = after[key]
        if old_value == new_value:
            continue
        if not isinstance(old_value, (int, float)) or not isinstance(new_value, (int, float)):
            add_change(
                changes,
                "major",
                "constraint_type_changed",
                pointer(path, key),
                f"{key} changed type: {old_value!r} -> {new_value!r}",
            )
            continue

        stricter = new_value > old_value if larger_is_stricter else new_value < old_value
        if stricter:
            add_change(
                changes,
                "major",
                "constraint_tightened",
                pointer(path, key),
                f"{key} tightened: {old_value} -> {new_value}",
            )
        else:
            add_change(
                changes,
                "minor",
                "constraint_relaxed",
                pointer(path, key),
                f"{key} relaxed: {old_value} -> {new_value}",
            )


def compare_schemas(before, after, path: str = "#"):
    changes = []

    if before == after:
        return changes

    if not isinstance(before, dict) or not isinstance(after, dict):
        add_change(
            changes,
            "major",
            "schema_node_changed",
            path,
            f"schema node changed from {type(before).__name__} to {type(after).__name__}",
        )
        return changes

    before_types = normalize_types(before.get("type"))
    after_types = normalize_types(after.get("type"))
    if before_types != after_types:
        widened = before_types and before_types.issubset(after_types)
        severity = "minor" if widened else "major"
        add_change(
            changes,
            severity,
            "type_changed",
            pointer(path, "type"),
            f"type changed: {sorted(before_types)} -> {sorted(after_types)}",
        )

    before_enum = before.get("enum")
    after_enum = after.get("enum")
    if isinstance(before_enum, list) and isinstance(after_enum, list):
        removed = sorted({json.dumps(v, sort_keys=True) for v in before_enum} - {json.dumps(v, sort_keys=True) for v in after_enum})
        added = sorted({json.dumps(v, sort_keys=True) for v in after_enum} - {json.dumps(v, sort_keys=True) for v in before_enum})
        if removed:
            add_change(
                changes,
                "major",
                "enum_value_removed",
                pointer(path, "enum"),
                f"enum values removed: {removed}",
            )
        if added:
            add_change(
                changes,
                "minor",
                "enum_value_added",
                pointer(path, "enum"),
                f"enum values added: {added}",
            )
    elif before_enum != after_enum and (before_enum is not None or after_enum is not None):
        add_change(
            changes,
            "major",
            "enum_definition_changed",
            pointer(path, "enum"),
            "enum definition changed",
        )

    if before.get("const") != after.get("const"):
        add_change(changes, "major", "const_changed", pointer(path, "const"), "const changed")

    before_required = set(before.get("required", [])) if isinstance(before.get("required"), list) else set()
    after_required = set(after.get("required", [])) if isinstance(after.get("required"), list) else set()
    for key in sorted(before_required - after_required):
        add_change(
            changes,
            "major",
            "required_removed",
            pointer(path, "required"),
            f"required field removed: {key}",
        )
    for key in sorted(after_required - before_required):
        add_change(
            changes,
            "major",
            "required_added",
            pointer(path, "required"),
            f"required field added: {key}",
        )

    before_props = before.get("properties", {}) if isinstance(before.get("properties"), dict) else {}
    after_props = after.get("properties", {}) if isinstance(after.get("properties"), dict) else {}
    for key in sorted(set(before_props) - set(after_props)):
        add_change(
            changes,
            "major",
            "property_removed",
            pointer(path, "properties"),
            f"property removed: {key}",
        )
    for key in sorted(set(after_props) - set(before_props)):
        severity = "major" if key in after_required else "minor"
        change_type = "required_property_added" if key in after_required else "optional_property_added"
        add_change(
            changes,
            severity,
            change_type,
            pointer(path, "properties"),
            f"property added: {key}",
        )
    for key in sorted(set(before_props) & set(after_props)):
        changes.extend(compare_schemas(before_props[key], after_props[key], pointer(pointer(path, "properties"), key)))

    compare_bounds(changes, before, after, path)

    for key in ["pattern", "format"]:
        if before.get(key) != after.get(key):
            add_change(
                changes,
                "major",
                "constraint_changed",
                pointer(path, key),
                f"{key} changed: {before.get(key)!r} -> {after.get(key)!r}",
            )

    before_additional = before.get("additionalProperties", True)
    after_additional = after.get("additionalProperties", True)
    if before_additional != after_additional:
        if before_additional is True and after_additional is False:
            severity = "major"
            detail = "additionalProperties tightened: true -> false"
        elif before_additional is False and after_additional is True:
            severity = "minor"
            detail = "additionalProperties relaxed: false -> true"
        else:
            severity = "major"
            detail = "additionalProperties changed"
        add_change(changes, severity, "additional_properties_changed", pointer(path, "additionalProperties"), detail)

    before_items = before.get("items")
    after_items = after.get("items")
    if isinstance(before_items, dict) and isinstance(after_items, dict):
        changes.extend(compare_schemas(before_items, after_items, pointer(path, "items")))
    elif before_items != after_items and (before_items is not None or after_items is not None):
        add_change(changes, "major", "items_changed", pointer(path, "items"), "items definition changed")

    for key in ["anyOf", "allOf", "oneOf", "not"]:
        if before.get(key) != after.get(key):
            add_change(changes, "major", "composition_changed", pointer(path, key), f"{key} changed")

    handled_keys = {
        "type",
        "enum",
        "const",
        "required",
        "properties",
        "minLength",
        "minimum",
        "exclusiveMinimum",
        "minItems",
        "maxLength",
        "maximum",
        "exclusiveMaximum",
        "maxItems",
        "pattern",
        "format",
        "additionalProperties",
        "items",
        "anyOf",
        "allOf",
        "oneOf",
        "not",
    }
    for key in sorted((set(before) | set(after)) - handled_keys - DOC_ONLY_KEYS - IGNORED_KEYS):
        if before.get(key) != after.get(key):
            add_change(
                changes,
                "major",
                "keyword_changed",
                pointer(path, key),
                f"keyword {key} changed",
            )

    return changes


def max_bump_from_changes(changes):
    current = "patch"
    for change in changes:
        candidate = change.get("severity", "patch")
        if candidate not in SEVERITY_ORDER:
            candidate = "patch"
        if SEVERITY_ORDER[candidate] > SEVERITY_ORDER[current]:
            current = candidate
    return current


def classify_pair(label: str, before_schema, after_schema, expected_bump=None):
    changes = compare_schemas(before_schema, after_schema, "#")
    if not changes and before_schema != after_schema:
        add_change(
            changes,
            "patch",
            "doc_or_non_semantic_update",
            "#",
            "no semantic keyword diff detected",
        )

    computed = max_bump_from_changes(changes)
    if before_schema == after_schema and not changes:
        computed = "patch"

    result = {
        "id": label,
        "expected_bump": expected_bump,
        "computed_bump": computed,
        "rationale": changes,
        "ok": True if expected_bump is None else expected_bump == computed,
    }
    return result


def classify_from_scenarios(input_path: Path):
    doc = load_json(input_path)
    results = []
    for scenario in doc.get("scenarios", []):
        result = classify_pair(
            label=scenario.get("id", "unknown"),
            before_schema=scenario.get("before_schema"),
            after_schema=scenario.get("after_schema"),
            expected_bump=scenario.get("expected_bump", "patch"),
        )
        result["description"] = scenario.get("description")
        results.append(result)
    return results


def classify_from_dirs(before_dir: Path, after_dir: Path):
    before_files = {p.name: p for p in sorted(before_dir.glob("*.schema.json")) if not is_metadata_path(p)}
    after_files = {p.name: p for p in sorted(after_dir.glob("*.schema.json")) if not is_metadata_path(p)}
    names = sorted(set(before_files) | set(after_files))

    results = []
    for name in names:
        if name not in before_files:
            result = {
                "id": name,
                "expected_bump": None,
                "computed_bump": "minor",
                "rationale": [
                    {
                        "severity": "minor",
                        "change_type": "schema_added",
                        "path": "#",
                        "detail": f"schema file added: {name}",
                    }
                ],
                "ok": True,
            }
            results.append(result)
            continue
        if name not in after_files:
            result = {
                "id": name,
                "expected_bump": None,
                "computed_bump": "major",
                "rationale": [
                    {
                        "severity": "major",
                        "change_type": "schema_removed",
                        "path": "#",
                        "detail": f"schema file removed: {name}",
                    }
                ],
                "ok": True,
            }
            results.append(result)
            continue

        result = classify_pair(
            label=name,
            before_schema=load_json(before_files[name]),
            after_schema=load_json(after_files[name]),
            expected_bump=None,
        )
        results.append(result)
    return results


def write_report(report: dict, output_dir: Path, explicit_report_path: str | None):
    output_dir.mkdir(parents=True, exist_ok=True)
    if explicit_report_path:
        out_path = Path(explicit_report_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        now = datetime.now(timezone.utc)
        out_path = output_dir / f"semver-classification-{now.strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    return out_path


def main():
    parser = argparse.ArgumentParser(description="Classify schema change impact as major/minor/patch")
    parser.add_argument(
        "--input",
        default="compatibility/fixtures/schema-change-scenarios.json",
        help="Path to scenario fixtures with before_schema/after_schema pairs",
    )
    parser.add_argument(
        "--before-dir",
        help="Directory containing previous schema files (*.schema.json)",
    )
    parser.add_argument(
        "--after-dir",
        help="Directory containing current schema files (*.schema.json)",
    )
    parser.add_argument(
        "--output-dir",
        default="compatibility/reports",
        help="Directory where classification report is written",
    )
    parser.add_argument(
        "--report",
        help="Optional explicit report path",
    )
    parser.add_argument(
        "--enforce-expected",
        action="store_true",
        help="Fail when computed bump differs from expected_bump (scenario mode only)",
    )
    args = parser.parse_args()

    mode = "scenario"
    if args.before_dir and args.after_dir:
        mode = "directory"
        results = classify_from_dirs(Path(args.before_dir), Path(args.after_dir))
    else:
        results = classify_from_scenarios(Path(args.input))

    mismatch_count = 0
    for item in results:
        if item.get("expected_bump") is not None and not item.get("ok"):
            mismatch_count += 1

    overall_bump = max_bump_from_changes(
        [{"severity": item.get("computed_bump", "patch")} for item in results]
    )
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "input": args.input if mode == "scenario" else None,
        "before_dir": args.before_dir if mode == "directory" else None,
        "after_dir": args.after_dir if mode == "directory" else None,
        "scenario_count": len(results),
        "mismatch_count": mismatch_count,
        "overall_bump": overall_bump,
        "results": results,
    }

    out_path = write_report(report, Path(args.output_dir), args.report)
    print(f"report written: {out_path}")
    print(
        f"mode={mode} scenario_count={len(results)} "
        f"mismatch_count={mismatch_count} overall_bump={overall_bump}"
    )

    if args.enforce_expected and mode == "scenario" and mismatch_count > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
