# Prerequisite Engine Specification

rule_type: course_prerequisite
conditions:
- learner attempts to enroll in a target course.
- target course has one or more prerequisite course rules configured.
- prerequisite rules may require any one course group (OR) or all listed courses (AND).
- prerequisite completion status is evaluated per learner transcript and recognized equivalency mappings.
enforcement_logic:
- build prerequisite graph for the target course and resolve aliases/equivalencies.
- evaluate each prerequisite node against learner records using completion state, minimum grade, and validity window.
- if all required nodes pass, set enrollment_decision=approved and persist evaluation audit.
- if any required node fails, set enrollment_decision=blocked, return unmet prerequisite list, and attach eligible bridge/remedial recommendations.
- support policy override path: instructor/admin override requires reason code and is fully audit-logged.

rule_type: learning_path_dependency
conditions:
- learner starts or advances within a structured learning path.
- path contains dependency edges between modules, milestones, or assessments.
- dependency types include sequential unlock, milestone gate, co-requisite, and score threshold.
- dependencies may be strict (hard block) or advisory (soft guidance).
enforcement_logic:
- represent the learning path as a directed acyclic dependency graph with node-level completion criteria.
- on each progression event, recompute unlock state for downstream nodes based on latest attempt outcomes and completion artifacts.
- for strict dependencies, lock downstream nodes until all upstream criteria are satisfied.
- for advisory dependencies, allow access but emit risk warning and flag learner for support nudges.
- prevent bypass loops by validating graph acyclicity at publish time and rejecting invalid path configurations.
- record all lock/unlock transitions with timestamp, dependency reason, and acting policy version for traceability.
