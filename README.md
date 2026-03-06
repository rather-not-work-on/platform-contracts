# platform-contracts

Shared contract source of truth for UAP multi-repo execution.

## Scope
- JSON Schema contracts C1~C8
- Contract fixture validation
- Compatibility and versioning policy baseline
- SemVer impact classification for schema changes

## Layout
- `schemas/`: C1~C8 schema files
- `fixtures/`: valid fixture samples for each contract
- `scripts/`: local contract validation scripts
- `compatibility/`: version policy and compatibility report

## Validation
```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_contracts.py --root .
python3 scripts/test_validate_contracts_strict.py
python3 scripts/classify_schema_change.py --enforce-expected
python3 scripts/test_classify_schema_change_diff.py
```
