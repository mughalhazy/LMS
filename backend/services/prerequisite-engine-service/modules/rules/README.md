# Prerequisite Rule Module

This module defines prerequisite and eligibility rule sets for the `prerequisite_engine_service`.

## Files

- `course-prerequisite.rules.json`: Enrollment gate rules based on prerequisite course completion, grade thresholds, equivalencies, and override policy.
- `learning-path-prerequisites.rules.json`: Path dependency graph rules covering strict/advisory edges, unlock logic, and acyclic publish-time constraints.
- `completion-eligibility.rules.json`: Completion-based eligibility rules for certificates or program enrollment targets.
- `rule-validation.schema.json`: Shared JSON schema envelope for all rule files.
- `validate_rules.py`: Runtime semantic validation (required fields, unique IDs, operator checks, graph cycle detection).

## Validation

```bash
python3 backend/services/prerequisite-engine-service/modules/rules/validate_rules.py
```

