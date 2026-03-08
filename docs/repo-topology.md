# platform-contracts Topology

## Purpose
Define deterministic ownership boundaries for the shared contract authority repository.

The goal is to make future schema/versioning work land in predictable places without re-deciding structure each time.

## Module Map
| Path | Responsibility | Allowed contents | Must not contain |
| --- | --- | --- | --- |
| `schemas/` | Canonical JSON Schema contracts consumed by other repos | `*.schema.json` contract files | fixtures, reports, ad hoc notes |
| `fixtures/` | Schema validation samples and negative fixtures | `*.valid.json`, `invalid/**` fixtures | production contracts, generated reports |
| `scripts/` | Repeatable local validation/publication tooling | validators, regression tests, publication helpers | runtime app logic, one-off migration notes |
| `compatibility/` | Human-readable compatibility policy, runbooks, and static maps | policy markdown, pin maps, publication runbooks | generated validation outputs, executable runtime state |
| `docs/` | Repository topology and operator-facing structure guidance | topology and extension guides | generated artifacts, schema fixtures |

## Naming Rules
- Schemas: `<contract-name>.schema.json`
- Valid fixtures: `<contract-name>.valid.json`
- Test entrypoints: `test_*.py` or `test_*.sh`
- Reports: generated under `compatibility/reports/*.json` only, never committed

## Extension Rules
1. Add or change contract definitions in `schemas/`.
2. Add/update matching fixtures in `fixtures/`.
3. Put validator and publication logic in `scripts/`.
4. Record compatibility policy or operator guidance in `compatibility/`.
5. Update the relevant module README when the module scope changes.

## Ownership Boundary
- `platform-contracts` owns contract definition, validation, and compatibility policy.
- Consumer runtime behavior belongs in consuming repositories, not here.
- Generated evidence about bundle publication may be emitted from here, but it must remain under gitignored `compatibility/reports/` unless explicitly promoted.
