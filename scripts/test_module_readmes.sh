#!/usr/bin/env bash
set -euo pipefail

required_files=(
  "docs/repo-topology.md"
  "schemas/README.md"
  "fixtures/README.md"
  "scripts/README.md"
  "compatibility/README.md"
)

for path in "${required_files[@]}"; do
  if [[ ! -f "$path" ]]; then
    echo "missing required topology file: $path"
    exit 1
  fi
done

grep -q '`docs/repo-topology.md`' README.md
grep -q 'Generated validation reports land under `compatibility/reports/` and are gitignored.' README.md
grep -q '| `schemas/` |' docs/repo-topology.md
grep -q '| `fixtures/` |' docs/repo-topology.md
grep -q '| `scripts/` |' docs/repo-topology.md
grep -q '| `compatibility/` |' docs/repo-topology.md

echo "module README topology contract ok"
