# platform-contracts

Shared contract source of truth for UAP multi-repo execution.

## Scope
- JSON Schema contracts C1~C8
- Contract fixture validation
- Compatibility and versioning policy baseline

## Layout
- `schemas/`: C1~C8 schema files
- `fixtures/`: valid fixture samples for each contract
- `scripts/`: local contract validation scripts
- `compatibility/`: version policy and compatibility report

## Validation
```bash
python3 scripts/validate_contracts.py --root .
```
