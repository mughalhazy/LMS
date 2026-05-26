# Prerequisite Engine Specification

**Type:** Service Specification | **Last reviewed:** 2026-05-26

Business rules and enforcement logic for the prerequisite engine. Covers course prerequisites and learning path dependencies.

---

## Rule: course_prerequisite

**Conditions:**
- Learner attempts to enroll in a target course.
- Target course has one or more prerequisite course rules configured.
- Prerequisite rules may require any one course group (OR) or all listed courses (AND).
- Prerequisite completion status is evaluated per learner transcript and recognized equivalency mappings.

**Enforcement logic:**
1. Build prerequisite graph for the target course and resolve aliases/equivalencies.
2. Evaluate each prerequisite node against learner records using completion state, minimum grade, and validity window.
3. If all required nodes pass: set `enrollment_decision=approved` and persist evaluation audit.
4. If any required node fails: set `enrollment_decision=blocked`, return unmet prerequisite list, and attach eligible bridge/remedial recommendations.
5. Support policy override path: instructor/admin override requires reason code and is fully audit-logged.

---

## Rule: learning_path_dependency

**Conditions:**
- Learner starts or advances within a structured learning path.
- Path contains dependency edges between modules, milestones, or assessments.
- Dependency types include sequential unlock, milestone gate, co-requisite, and score threshold.
- Dependencies may be strict (hard block) or advisory (soft guidance).

**Enforcement logic:**
1. Represent the learning path as a directed acyclic dependency graph with node-level completion criteria.
2. On each progression event, recompute unlock state for downstream nodes based on latest attempt outcomes and completion artifacts.
3. For strict dependencies: lock downstream nodes until all upstream criteria are satisfied.
4. For advisory dependencies: allow access but emit risk warning and flag learner for support nudges.
5. Prevent bypass loops by validating graph acyclicity at publish time and rejecting invalid path configurations.
6. Record all lock/unlock transitions with timestamp, dependency reason, and acting policy version for traceability.
