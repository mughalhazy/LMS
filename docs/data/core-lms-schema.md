# Core LMS Relational Schema

**Location:** `Repo/docs/data/core-lms-schema.md` | **Type:** Data Spec | **Last reviewed:** 2026-05-26

Heritage relational schema for the LMS platform. Represents the Rails Enterprise LMS V2 base tables that all services extend above. Index definitions, lifecycle policies, and ownership boundaries are tracked in service-level migration docs.

## Schema

| table_name | primary_key | relationships |
| --- | --- | --- |
| tenants | tenant_id | 1:N with organizations, users, courses, assessments, certificates |
| organizations | organization_id | N:1 to tenants (tenant_id), 1:N with users and courses |
| users | user_id | N:1 to tenants (tenant_id), N:1 to organizations (organization_id), 1:N with enrollments and certificates |
| courses | course_id | N:1 to tenants (tenant_id), N:1 to organizations (organization_id), 1:N with lessons, enrollments, and assessments |
| lessons | lesson_id | **tenant_id NOT NULL** (CAT-015: first-class tenant column required — isolation must not rely solely on course FK per multi-tenant-isolation-model.md). N:1 to tenants (tenant_id), N:1 to courses (course_id). Unique: (tenant_id, course_id, lesson_id). |
| enrollments | enrollment_id | **tenant_id NOT NULL** (CAT-016: tenant_id mandatory in unique constraint). N:1 to tenants (tenant_id), N:1 to users (user_id), N:1 to courses (course_id). Unique: **(tenant_id, user_id, course_id)** — tenant_id scopes uniqueness to prevent cross-tenant collisions. |
| assessments | assessment_id | N:1 to tenants (tenant_id), N:1 to courses (course_id), optional N:1 to lessons (lesson_id) |
| certificates | certificate_id | N:1 to tenants (tenant_id), N:1 to users (user_id), N:1 to courses (course_id), optional N:1 to enrollments (enrollment_id). Unique: (tenant_id, user_id, course_id). |
