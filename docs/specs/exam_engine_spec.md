# Exam Engine Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5.1 | **Service:** `services/exam-engine/`

---

## Scope

The exam engine handles secure, high-stakes assessment delivery. It is distinct from the assessment service (which owns question banks, scoring, and attempt records) — the exam engine handles the delivery session, proctoring rules, and timing controls.

---

## Capabilities Defined

### CAP-EXAM-DELIVERY
- Secure exam session delivery with question sequencing, time limits, and submission enforcement
- Integrates with assessment service for question content and attempt recording
- Shared model: `shared/models/exam_session.py`

### CAP-PROCTORING-RULES
- Configurable exam integrity controls: single-window enforcement, copy-paste disable, time-per-question limits, IP restrictions
- All rules are config-driven — stored in config service per capability key

### CAP-ATTEMPT-LIFECYCLE
- Manage exam attempt states: started → in-progress → submitted → graded
- Handles: resume tokens, timeout handling, connection loss recovery
- Emits: `exam.attempt_started`, `exam.submitted`, `exam.timed_out`

---

## Service Files

- `services/exam-engine/service.py`
- `services/exam-engine/models.py`
- `services/exam-engine/qc.py`
- `services/exam-engine/test_exam_engine.py`

---

## References

- Master Spec §5.1
- `docs/specs/assessment_service_spec.md`
- `docs/data/DATA_06_assessment_data_schema.md`
