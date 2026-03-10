# Contract Bundle Publication Runbook

Canonical reference has moved to `compatibility/publish-and-pin-runbook.md`.
This file is kept as a compatibility alias.

## Goal
Publish deterministic contract bundle evidence and verify that consumer repositories pin the same bundle version before federation checks run.

## Inputs
- schemas: `schemas/*.schema.json`
- consumer pin map: `compatibility/consumer-pin-map.json`
- consumer pin files:
  - `platform-provider-gateway/config/contract-pin.json`
  - `platform-observability-gateway/config/contract-pin.json`
  - `monday/contracts/contract-pin.json`

## Publication Command
```bash
python3 scripts/publish_contract_bundle.py \
  --bundle-version 2026.03.07 \
  --workspace-root .. \
  --strict
```

## Outputs
- `compatibility/reports/contract-bundle-<bundle_version>.json`
- `compatibility/reports/consumer-contract-pins-<bundle_version>.json`

## Review Checklist
1. `bundle_version` matches intended release date/version.
2. all schema files appear in bundle evidence with `sha256`.
3. all consumer pin files reference the same `bundle_version`.
4. `pinned_contracts` is non-empty for every consumer repo.

## Validation
```bash
python3 scripts/validate_contracts.py --root .
python3 scripts/test_validate_contracts_strict.py
python3 scripts/test_publish_contract_bundle.py
```

## Failure Handling
- `pin_file_missing`: consumer repository has not committed its contract pin.
- `bundle_version_mismatch`: consumer repository still points at an older contract release.
- `pinned_contracts_missing`: consumer repository pin file exists but does not declare consumed contracts.
