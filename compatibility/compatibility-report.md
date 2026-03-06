# C1~C8 Compatibility Report

## Versioning Rules
- major: required field removal/rename, enum semantic changes
- minor: optional field additions
- patch: documentation/example/non-semantic corrections

## Guardrails
- required keys in C1~C8 cannot be removed without major bump
- enum additions require consumer fallback behavior checks
- unknown optional keys must not break consumers

## Current Baseline
- contract set: C1, C2, C3, C4, C5, C6, C7, C8
- baseline version: `1.0.0`
- validation command:

```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_contracts.py --root .
python3 scripts/test_validate_contracts_strict.py
```

- strictness policy:
  - `compatibility/schema-strictness-policy.md`

## SemVer Classification Automation
- policy: `compatibility/semver-policy.md`
- classifier command:

```bash
python3 scripts/classify_schema_change.py --enforce-expected
```

- fixed report path:
  - `compatibility/reports/semver-classification-<timestamp>.json`

## Change Checklist
- [ ] schema diff reviewed
- [ ] compatibility impact classification assigned (major/minor/patch)
- [ ] fixture validation passes
- [ ] downstream consumers acknowledged
