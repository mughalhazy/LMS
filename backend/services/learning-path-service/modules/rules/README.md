# Learning Path Progression Rules

This module defines progression rules for the Learning Path Service.

## Implemented rule families

1. **Sequential progression**
   - Strict unlock for required nodes after upstream completion + score checks.
2. **Optional branching**
   - Branch availability with elective group min/max enforcement and explicit merge validation.
3. **Prerequisite validation**
   - Runtime dependency evaluation with strict/advisory enforcement, equivalency resolution, and override auditing.

## Source alignment

Rules are derived from:
- `docs/specs/learning_path_spec.md`
- `docs/specs/prerequisite_engine_spec.md`

## Output contract

- `files_created`
  - `backend/services/learning-path-service/modules/rules/progression_rules.json`
  - `backend/services/learning-path-service/modules/rules/README.md`
- `rules_defined`
  - `LP-SEQ-001`
  - `LP-BR-001`
  - `LP-PR-001`
