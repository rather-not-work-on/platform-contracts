# scripts

## Responsibility
Host repeatable validation, compatibility, and publication tooling for `platform-contracts`.

## Contents
- schema validators
- SemVer diff classification
- contract bundle publication helpers
- regression tests

## Rules
- scripts are local tooling, not runtime application logic
- default outputs must land in gitignored report locations
- every contract-impacting behavior change should add or update a regression test
