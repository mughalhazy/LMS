issue_type
entity_or_table
description
severity
recommended_fix

Missing core entity
learning_paths
Analytics and progress events (`ProgressSnapshotUpdated`, `PathMilestoneAchieved`) reference `learning_path_id`, but no `learning_paths` table exists in core schema.
high
Add `learning_paths` (and `path_nodes`/junction tables as needed) with tenant/org ownership and FK references from progress/completion records.

Missing core entity
cohorts
Analytics events (`CohortAssignmentCreated`, `CohortEngagementMeasured`) require `cohort_id`, but no cohort/group table exists in core schema.
high
Add `cohorts` and `cohort_memberships` tables and enforce FK integrity for cohort analytics events.

Missing core entity
skills
Skill analytics events (`SkillEvidenceLogged`, `SkillProficiencyUpdated`, `SkillGapIdentified`) reference `skill_id` and role-skill mappings that are absent from schema.
high
Add `skills`, `learner_skills`, and `role_skill_requirements` tables (or define external source-of-truth with replicated dimension tables).

Missing core entity
roles
`SkillGapIdentified` includes `role_id`, but no `roles` table is present in core schema.
medium
Add a `roles` table (or reference identity domain table) and document ownership/boundary in schema.

Invalid/weak relationship mapping
assessments -> learners
`AssessmentAttemptSubmitted` event uses `attempt_id` and learner attempts, but relational schema has no `assessment_attempts` table linking users to assessments.
high
Add `assessment_attempts` with FKs to `users`, `assessments`, and optionally `enrollments`.

Naming mismatch (relationship risk)
lessons vs module_id
Multiple analytics events reference `module_id`, while core schema models `lessons` only; this can break joins and semantic consistency.
medium
Standardize on one canonical concept (`lesson` or `module`), update event schema fields, and provide backward-compatible aliases during migration.

Potential duplicate domain concepts
certificates vs certifications
Core schema uses `certificates`, while service/domain docs use `certification` entities; risk of parallel tables/services representing same lifecycle.
medium
Converge naming and ownership to a single certification model (`certifications` + `issuance_records`) and deprecate duplicates.

Analytics-event coverage gap
Enrollment lifecycle events
Core transactional entity `enrollments` exists, but analytics model lacks explicit enrollment lifecycle events (assigned/approved/waitlisted/cancelled), reducing funnel observability.
medium
Add events such as `EnrollmentRequested`, `EnrollmentApproved`, `EnrollmentWaitlisted`, `EnrollmentCancelled` with consistent IDs and timestamps.

Analytics-event coverage gap
Certificate issuance/revocation events
Schema includes certificates, but analytics model has no explicit issuance/revocation/expiration events tied to certification lifecycle.
medium
Add `CertificateIssued`, `CertificateRevoked`, and `CertificateExpired` events mapped to certification tables.

No duplicate tables detected
core_lms_schema tables
Current core schema table list does not contain exact duplicate table names.
info
Keep naming governance checks in CI (lint/schema-diff) to prevent future duplicate table introductions.
