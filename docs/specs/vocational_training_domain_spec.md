# Vocational Training Domain Spec

**Type:** Specification | **Date:** 2026-04-14 | **MS§:** §5.19 (Use-case Capability Domain Extension)
**Gap:** MO-015 | **Source authority:** `LMS_Pakistan_Market_Research_MASTER.md` §3.3 (Vocational segment)
**Status:** PLANNED — no service built yet

---

## Purpose

This spec defines the capability domain for vocational training institutions — nursing, IT certifications, digital marketing, trades (plumbing, electrical), and professional upskilling programs.

Per the Pakistan market research, vocational training is the **most underserved niche** in the LMS market: the segment is growing rapidly but has almost no dedicated LMS infrastructure. The platform must extend its capability bundle to address vocational-specific requirements without creating a segment-forked product.

---

## Domain Identity

This domain is a **capability domain extension** (B5P* pattern) — it extends the core platform by activating additional capabilities for tenants configured for vocational training. It does not fork the platform or create a segment-specific product.

**Tenant signal:** `segment_type = "vocational"` activates this domain's default capability bundle.

---

## Core Pain Points Addressed

| Pain Point | Market Evidence | Capability Response |
|---|---|---|
| Certification tracking is weak or absent | Market Research §3.3 | CAP-VOCATIONAL-CERT-TRACKING |
| Placement tracking is missing | Market Research §3.3 | CAP-VOCATIONAL-PLACEMENT-TRACKING |
| Course delivery is fragmented across tools | Market Research §3.3 | CAP-VOCATIONAL-STRUCTURED-PATHWAY |
| No compliance/regulatory proof of completion | Inferred from certification gap | CAP-VOCATIONAL-COMPLIANCE-CERT |
| Practical/hands-on assessment not supported | Vocational domain nature | CAP-VOCATIONAL-PRACTICAL-ASSESSMENT |

---

## Capabilities Defined

### CAP-VOCATIONAL-CERT-TRACKING
**Description:** Track learner progress toward recognized certifications, including external certification body requirements.
**What this enables:**
- Define a certification pathway with required modules, minimum scores, and practical components
- Track each learner's progress against pathway completion criteria
- Auto-flag learners who have met all criteria and are eligible for certification
- Issue platform certificates upon completion; flag external cert body requirements as a separate action item

**Implementation notes:**
- Extends `SPEC_14` (Certificate Service) with certification pathway model
- Pathway definition: ordered modules + minimum pass scores + practical sign-off requirements
- Status tracking: in_progress → eligible → issued → externally_verified

### CAP-VOCATIONAL-PLACEMENT-TRACKING
**Description:** Track learner placement outcomes — job offers, internships, self-employment — after course completion.
**What this enables:**
- Log placement outcomes per learner (employer, role type, placement date, salary band if available)
- Aggregate placement rate per batch and per course
- Surface placement rate as a key institutional metric on the analytics dashboard
- Allow operators to use placement data as a marketing signal (completion + placement rates visible to prospective students)

**Implementation notes:**
- New data entity: `PlacementRecord` (learner_id, tenant_id, course_id, batch_id, placement_type, employer, role, placement_date, verified_by_operator)
- Operator-entered data — no automated placement detection
- Feeds into CAP-VOCATIONAL-OUTCOMES-DASHBOARD

### CAP-VOCATIONAL-STRUCTURED-PATHWAY
**Description:** Structure vocational courses as ordered learning pathways with mandatory prerequisites and sign-off gates.
**What this enables:**
- Define sequential learning pathways (theory → lab → practical → assessment)
- Enforce prerequisite completion before advancing to next pathway stage
- Support hybrid delivery: some stages online, some in-person (flagged as "requires physical attendance")
- Allow instructors to sign off on practical stages that cannot be auto-assessed

**Implementation notes:**
- Extends `learning_path_spec.md` with a `vocational_pathway_type` flag
- Physical attendance stages: `delivery_mode = "in_person_required"`, instructor sign-off required before unlock
- Integrates with prerequisite engine (`prerequisite_engine_spec.md`)

### CAP-VOCATIONAL-PRACTICAL-ASSESSMENT
**Description:** Support practical/skills-based assessments that require instructor observation and manual grading.
**What this enables:**
- Define assessment events that cannot be auto-graded (observed practical demonstration, portfolio submission, live performance)
- Assign assessor to practical assessment events
- Assessor records pass/fail with optional notes
- Practical assessment outcome feeds into pathway completion logic

**Implementation notes:**
- Extends `assessment_service_spec.md` with `assessment_type = "practical"`
- `grading_mode = "manual"` with required `assessor_id` assignment
- Assessor sign-off triggers pathway unlock for next stage

### CAP-VOCATIONAL-COMPLIANCE-CERT
**Description:** Generate compliance-grade completion certificates that include regulatory and certification body-required metadata.
**What this enables:**
- Certificates include: course name, completion date, total hours, assessment scores, practical sign-offs, issuing institution, assessor details
- PDF generation with tamper-evident QR code verification
- Certificate registry queryable by external parties via public verification link

**Implementation notes:**
- Extends `SPEC_14` with `certificate_type = "vocational_compliance"`
- Mandatory fields: `total_training_hours`, `practical_component_hours`, `assessor_name`, `assessor_credential`
- QR code links to public verification endpoint (read-only, no auth required)

### CAP-VOCATIONAL-OUTCOMES-DASHBOARD
**Description:** Aggregate vocational-specific outcomes — completion rates, certification rates, placement rates — as the primary dashboard for vocational institution operators.
**What this enables:**
- Dashboard shows: active learners, completion rate (current cohort), certification eligibility queue, placement rate (all-time + last 90 days)
- Per-batch breakdown for each metric
- MS-UX-02 compliant: each metric carries a suggested action

**Implementation notes:**
- Reads from: progress records, placement records, certificate records
- Feeds the Daily Action List with: certification eligibility queue, practical assessment sign-off queue

---

## Default Capability Bundle (vocational segment)

When `segment_type = "vocational"` is set on a tenant, the following capabilities are activated by default:

| Capability | Default State | Rationale |
|---|---|---|
| CAP-VOCATIONAL-CERT-TRACKING | ON | Core vocational need |
| CAP-VOCATIONAL-PLACEMENT-TRACKING | ON | Core vocational differentiator |
| CAP-VOCATIONAL-STRUCTURED-PATHWAY | ON | Required for sequential vocational delivery |
| CAP-VOCATIONAL-PRACTICAL-ASSESSMENT | ON | Required for trade/skills programs |
| CAP-VOCATIONAL-COMPLIANCE-CERT | ON | Regulatory expectation |
| CAP-VOCATIONAL-OUTCOMES-DASHBOARD | ON | Replaces generic dashboard for vocational operators |

---

## Behavioral Contracts

This domain operates within the following platform behavioral contracts:

- **BC-EXAM-01:** Practical assessment sign-off sessions must be inviolable (no gate interruptions mid-assessor-session)
- **BC-LEARN-01:** Progress visibility must include certification eligibility and placement status, not just module completion
- **MS-UX-02:** Placement rate and certification queue must appear with suggested actions, not as bare metrics

---

## Implementation Dependency

This spec depends on:
- `SPEC_14` (Certificate Service) — extends it
- `learning_path_spec.md` — extends it
- `assessment_service_spec.md` — extends it
- `prerequisite_engine_spec.md` — extends it
- `B0P09_full_capability_domain_map.md` — domain must be registered here when built

---

## References

- `LMS_Pakistan_Market_Research_MASTER.md` §3.3 (Vocational segment pain points)
- `docs/architecture/domain_capability_extension_model.md` — extension model
- `docs/specs/B0P09_full_capability_domain_map.md` — capability domain map
- `SPEC_14` — certificate service
- `docs/specs/learning_path_spec.md`
- `docs/specs/assessment_service_spec.md`
