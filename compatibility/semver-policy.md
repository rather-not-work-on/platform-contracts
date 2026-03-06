# Contract SemVer Policy

## Scope
Applies to C1~C8 schemas in `schemas/`.

## Classification Rules
- `major`
  - required field add/remove
  - property removal
  - type/constraint tightening
  - enum value removal
- `minor`
  - optional property addition
  - enum value addition
  - constraint relaxation
- `patch`
  - documentation/example/non-semantic corrections

## Classification Engine
- Runtime classification uses schema `before/after` diff, not fixed change labels.
- Evidence output includes per-schema and per-path rationale:
  - `id` (scenario or schema file name)
  - `computed_bump`
  - `rationale[]` with `severity`, `change_type`, `path`, `detail`

### Commands
- Scenario regression (CI gate):
  - `python3 scripts/classify_schema_change.py --enforce-expected`
  - `python3 scripts/test_classify_schema_change_diff.py`
- Directory diff (release decision):
  - `python3 scripts/classify_schema_change.py --before-dir <prev_schemas_dir> --after-dir schemas`

## CI Contract
Every PR must pass:
1. `python3 -m pip install -r requirements-dev.txt`
2. `python3 scripts/validate_contracts.py --root .`
3. `python3 scripts/test_validate_contracts_strict.py`
4. `python3 scripts/classify_schema_change.py --enforce-expected`
5. `python3 scripts/test_classify_schema_change_diff.py`

## Fixed Report Path Contract
Classification reports are emitted to:
- `compatibility/reports/semver-classification-<timestamp>.json`

This path is the canonical evidence location for issue #17 acceptance.
