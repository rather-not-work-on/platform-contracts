#!/usr/bin/env python3

import json
import subprocess
import tempfile
from pathlib import Path

from jsonschema_compat import load_validator_exports

Draft202012Validator, FormatChecker, _ = load_validator_exports()


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def run_publish(workspace_root: Path, pin_map: Path, bundle_output: Path, pin_output: Path, strict: bool = True):
    cmd = [
        "python3",
        "scripts/publish_contract_bundle.py",
        "--bundle-version",
        "2026.03.07",
        "--workspace-root",
        str(workspace_root),
        "--pin-map",
        str(pin_map),
        "--bundle-output",
        str(bundle_output),
        "--pin-output",
        str(pin_output),
    ]
    if strict:
        cmd.append("--strict")
    return subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)


def main():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_root = Path(tmp_dir)
        workspace_root = tmp_root / "workspace"
        (workspace_root / "platform-provider-gateway" / "config").mkdir(parents=True, exist_ok=True)
        (workspace_root / "platform-observability-gateway" / "config").mkdir(parents=True, exist_ok=True)
        (workspace_root / "monday" / "contracts").mkdir(parents=True, exist_ok=True)

        pin_docs = {
            workspace_root / "platform-provider-gateway" / "config" / "contract-pin.json": {
                "source_repo": "rather-not-work-on/platform-contracts",
                "contract_bundle_version": "2026.03.07",
                "pinned_contracts": ["c4-provider-invocation"],
                "consumer_repo": "rather-not-work-on/platform-provider-gateway",
            },
            workspace_root / "platform-observability-gateway" / "config" / "contract-pin.json": {
                "source_repo": "rather-not-work-on/platform-contracts",
                "contract_bundle_version": "2026.03.07",
                "pinned_contracts": ["c5-observability-event"],
                "consumer_repo": "rather-not-work-on/platform-observability-gateway",
            },
            workspace_root / "monday" / "contracts" / "contract-pin.json": {
                "source_repo": "rather-not-work-on/platform-contracts",
                "contract_bundle_version": "2026.03.07",
                "pinned_contracts": ["c1-run-lifecycle", "c2-subtask-handoff"],
                "consumer_repo": "rather-not-work-on/monday",
            },
        }
        for path, doc in pin_docs.items():
            path.write_text(json.dumps(doc, ensure_ascii=True, indent=2), encoding="utf-8")

        pin_map = tmp_root / "consumer-pin-map.json"
        pin_map.write_text(
            json.dumps(
                {
                    "source_repo": "rather-not-work-on/platform-contracts",
                    "consumers": [
                        {
                            "consumer_repo": "rather-not-work-on/platform-provider-gateway",
                            "pin_path": "platform-provider-gateway/config/contract-pin.json",
                        },
                        {
                            "consumer_repo": "rather-not-work-on/platform-observability-gateway",
                            "pin_path": "platform-observability-gateway/config/contract-pin.json",
                        },
                        {
                            "consumer_repo": "rather-not-work-on/monday",
                            "pin_path": "monday/contracts/contract-pin.json",
                        },
                    ],
                },
                ensure_ascii=True,
                indent=2,
            ),
            encoding="utf-8",
        )

        bundle_output = tmp_root / "bundle.json"
        pin_output = tmp_root / "pins.json"
        completed = run_publish(workspace_root, pin_map, bundle_output, pin_output)
        if completed.returncode != 0:
            raise AssertionError(completed.stderr or completed.stdout)

        bundle_doc = load_json(bundle_output)
        pin_doc = load_json(pin_output)
        bundle_schema = load_json(REPO_ROOT / "schemas" / "contract-bundle-evidence.schema.json")
        pin_schema = load_json(REPO_ROOT / "schemas" / "consumer-contract-pin-evidence.schema.json")
        Draft202012Validator(bundle_schema, format_checker=FormatChecker()).validate(bundle_doc)
        Draft202012Validator(pin_schema, format_checker=FormatChecker()).validate(pin_doc)
        if bundle_doc["schema_count"] < 8:
            raise AssertionError("bundle should include existing contract schemas")
        if any(row["verdict"] != "pass" for row in pin_doc["consumer_results"]):
            raise AssertionError("all pin results should pass in valid fixture")

        broken_pin = workspace_root / "monday" / "contracts" / "contract-pin.json"
        broken_doc = load_json(broken_pin)
        broken_doc["contract_bundle_version"] = "2026.02.28"
        broken_pin.write_text(json.dumps(broken_doc, ensure_ascii=True, indent=2), encoding="utf-8")

        failed = run_publish(workspace_root, pin_map, bundle_output, pin_output)
        if failed.returncode == 0:
            raise AssertionError("expected strict failure when consumer pin version mismatches")

    print("contract bundle publication regression checks passed")


if __name__ == "__main__":
    main()
