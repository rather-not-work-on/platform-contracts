# Schema Strictness Policy

## Goal
Ensure contract fixtures are validated with deterministic JSON Schema rules, not partial key checks.

## Baseline Rules
- All C1~C8 top-level schemas set `additionalProperties: false`.
- Required identifiers use `minLength` or `minimum` constraints.
- UTC timestamp fields use JSON Schema `format: date-time`.
- Contract version fields use semver pattern checks where applicable.

## Explicit Flexibility Zones
Some nested objects remain extensible by design:
- `c2.constraints`
- `c3.metrics`

These are open maps because producers can add execution-specific knobs/metrics without breaking consumers.

## Change Process
When changing strictness:
1. Update schema files.
2. Update fixtures and validation scripts.
3. Record compatibility impact using `scripts/classify_schema_change.py`.
4. Keep rationale in this document when allowing `additionalProperties: true`.

