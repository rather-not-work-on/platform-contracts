#!/usr/bin/env python3

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import sys


SOURCE_REPO = "rather-not-work-on/platform-contracts"
DEFAULT_PIN_MAP = Path("compatibility/consumer-pin-map.json")
DEFAULT_REPORT_DIR = Path("compatibility/reports")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def utc_bundle_version() -> str:
    return datetime.now(timezone.utc).strftime("%Y.%m.%d")


def resolve_repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in [current] + list(current.parents):
        if (candidate / ".git").exists():
            return candidate
    return Path(__file__).resolve().parents[1]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_hex(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_bundle_doc(repo_root: Path, bundle_version: str) -> dict:
    schemas = []
    for schema_path in sorted((repo_root / "schemas").glob("*.schema.json")):
        if schema_path.name.startswith("._") or schema_path.name == ".DS_Store":
            continue
        schema_doc = load_json(schema_path)
        contract_id = schema_doc.get("$id") or schema_path.name.replace(".schema.json", "")
        schemas.append(
            {
                "schema_name": schema_path.name,
                "contract_id": contract_id,
                "path": str(schema_path.relative_to(repo_root)),
                "sha256": sha256_hex(schema_path),
            }
        )

    return {
        "generated_at_utc": now_utc(),
        "source_repo": SOURCE_REPO,
        "bundle_version": bundle_version,
        "schema_count": len(schemas),
        "schemas": schemas,
    }


def evaluate_consumer_pin(bundle_version: str, workspace_root: Path, row: dict) -> dict:
    pin_path = workspace_root / row["pin_path"]
    result = {
        "consumer_repo": row["consumer_repo"],
        "pin_path": row["pin_path"],
        "verdict": "pass",
        "errors": [],
    }
    if not pin_path.exists():
        result["verdict"] = "fail"
        result["errors"].append("pin_file_missing")
        return result

    pin_doc = load_json(pin_path)
    result["contract_bundle_version"] = pin_doc.get("contract_bundle_version")
    result["pinned_contracts"] = pin_doc.get("pinned_contracts", [])

    if pin_doc.get("source_repo") != SOURCE_REPO:
        result["errors"].append("source_repo_mismatch")
    if pin_doc.get("consumer_repo") != row["consumer_repo"]:
        result["errors"].append("consumer_repo_mismatch")
    if pin_doc.get("contract_bundle_version") != bundle_version:
        result["errors"].append("bundle_version_mismatch")
    if not isinstance(pin_doc.get("pinned_contracts"), list) or not pin_doc.get("pinned_contracts"):
        result["errors"].append("pinned_contracts_missing")

    if result["errors"]:
        result["verdict"] = "fail"
    return result


def build_pin_doc(bundle_version: str, workspace_root: Path, pin_map_path: Path) -> dict:
    pin_map = load_json(pin_map_path)
    consumers = pin_map.get("consumers", [])
    results = [evaluate_consumer_pin(bundle_version, workspace_root, row) for row in consumers]
    return {
        "generated_at_utc": now_utc(),
        "source_repo": SOURCE_REPO,
        "bundle_version": bundle_version,
        "consumer_count": len(results),
        "consumer_results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish contract bundle evidence and consumer pin evidence")
    parser.add_argument("--bundle-version", default=utc_bundle_version())
    parser.add_argument("--workspace-root", default="..")
    parser.add_argument("--pin-map", default=str(DEFAULT_PIN_MAP))
    parser.add_argument("--bundle-output", default=None)
    parser.add_argument("--pin-output", default=None)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    repo_root = resolve_repo_root()
    workspace_root = (repo_root / args.workspace_root).resolve()
    pin_map_path = Path(args.pin_map)
    if not pin_map_path.is_absolute():
        pin_map_path = repo_root / pin_map_path

    bundle_doc = build_bundle_doc(repo_root, args.bundle_version)
    pin_doc = build_pin_doc(args.bundle_version, workspace_root, pin_map_path)

    report_dir = repo_root / DEFAULT_REPORT_DIR
    bundle_output = Path(args.bundle_output) if args.bundle_output else report_dir / f"contract-bundle-{args.bundle_version}.json"
    pin_output = Path(args.pin_output) if args.pin_output else report_dir / f"consumer-contract-pins-{args.bundle_version}.json"

    bundle_output.parent.mkdir(parents=True, exist_ok=True)
    pin_output.parent.mkdir(parents=True, exist_ok=True)
    bundle_output.write_text(json.dumps(bundle_doc, ensure_ascii=True, indent=2), encoding="utf-8")
    pin_output.write_text(json.dumps(pin_doc, ensure_ascii=True, indent=2), encoding="utf-8")

    pin_failures = [row for row in pin_doc["consumer_results"] if row["verdict"] != "pass"]
    verdict = "pass" if bundle_doc["schema_count"] > 0 and not pin_failures else "fail"

    print(f"bundle report written: {bundle_output}")
    print(f"pin report written: {pin_output}")
    print(
        f"bundle_version={args.bundle_version} schema_count={bundle_doc['schema_count']} "
        f"consumer_count={pin_doc['consumer_count']} pin_failures={len(pin_failures)} verdict={verdict}"
    )
    if args.strict and verdict != "pass":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
