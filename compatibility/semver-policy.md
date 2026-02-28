# Contract SemVer Policy

## Scope
Applies to C1~C8 schemas in `schemas/`.

## Classification Rules
- `major`
  - required field removal or rename
  - enum semantic meaning change
- `minor`
  - optional field addition
  - enum value addition when consumer fallback is confirmed
- `patch`
  - documentation/example/non-semantic corrections

## CI Contract
Every PR must pass:
1. `python3 scripts/validate_contracts.py --root .`
2. `python3 scripts/classify_schema_change.py --enforce-expected`

## Fixed Report Path Contract
Classification reports are emitted to:
- `compatibility/reports/semver-classification-<timestamp>.json`

This path is the canonical evidence location for issue #17 acceptance.
