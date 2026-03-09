# platform-contracts

Shared contract source of truth for UAP multi-repo execution.

## Scope
- JSON Schema contracts C1~C8
- Contract bundle publication and consumer pin evidence
- Contract fixture validation
- Compatibility and versioning policy baseline
- SemVer impact classification for schema changes

## Layout
- `schemas/`: C1~C8 schema files
- `fixtures/`: valid fixture samples for each contract
- `scripts/`: local contract validation scripts
- `compatibility/`: version policy and compatibility report
- `docs/`: topology and extension guidance

Topology guide:
- `docs/repo-topology.md`
- `schemas/README.md`
- `fixtures/README.md`
- `scripts/README.md`
- `compatibility/README.md`

## Validation
```bash
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_contracts.py --root .
python3 scripts/test_validate_contracts_strict.py
python3 scripts/classify_schema_change.py --enforce-expected
python3 scripts/test_classify_schema_change_diff.py
python3 scripts/test_publish_contract_bundle.py
bash scripts/test_module_readmes.sh
```

## Publication
```bash
python3 scripts/publish_contract_bundle.py --bundle-version 2026.03.07 --workspace-root .. --strict
```

Runbook:
- `compatibility/contract-bundle-publication-runbook.md`

## PR Hygiene
- template: `.github/pull_request_template.md`
- review gate: `.github/workflows/pr-review-gate.yml`
- external repo PRs must include a repo-qualified planningops issue ref
- example: `Closes rather-not-work-on/platform-planningops#210`

Generated validation reports land under `compatibility/reports/` and are gitignored.
