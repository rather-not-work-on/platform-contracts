# Publish and Pin Runbook

## Goal
Publish deterministic contract bundle evidence and verify all consumer repositories pin the same `bundle_version` before federated checks run.

## Preconditions
- schemas and fixtures validate locally:
  - `python3 scripts/validate_contracts.py --root .`
  - `python3 scripts/test_validate_contracts_strict.py`
  - `python3 scripts/test_publish_contract_bundle.py`
- consumer pin map is current: `compatibility/consumer-pin-map.json`
- consumer pin files exist:
  - `platform-provider-gateway/config/contract-pin.json`
  - `platform-observability-gateway/config/contract-pin.json`
  - `monday/contracts/contract-pin.json`

## Publish Command
```bash
python3 scripts/publish_contract_bundle.py \
  --bundle-version 2026.03.07 \
  --workspace-root .. \
  --strict
```

## Expected Outputs
- `compatibility/reports/contract-bundle-<bundle_version>.json`
- `compatibility/reports/consumer-contract-pins-<bundle_version>.json`

## Pin Verification Checklist
1. `bundle_version` matches the intended release tag/date.
2. every schema appears in bundle evidence with a `sha256` digest.
3. every consumer pin file declares the same `bundle_version`.
4. every consumer declares non-empty `pinned_contracts`.

## Failure Modes
- `pin_file_missing`: consumer repo is missing the contract pin file.
- `bundle_version_mismatch`: consumer still references an older bundle.
- `pinned_contracts_missing`: consumer pin file exists but has no consumed contracts.

## Conformance Note
Use this file as the canonical runbook for publication and consumer pin alignment checks in PlanningOps federated conformance parsing.
