# ARCH_04 Service Data Ownership Rules

## Purpose
Define canonical data ownership boundaries for Enterprise LMS V2 services so each entity has a single system-of-record owner.

## Service → Entity Ownership Matrix

| Service | Owned entities (system of record) |
|---|---|
| Identity Service | `User`, `AuthCredential` |
| Organization Service | `Institution` |
| Learning Structure Service | `Program`, `Cohort`, `Session` |
| Learning Runtime Service | `Course`, `Lesson`, `Enrollment`, `Progress` |
| Assessment Service | `Assessment`, `AttemptRecord` |
| Certification Service | `Certificate` |
| Analytics Service | `LearningEvent`, `AggregatedAnalytics` |
| AI Service | `AIInteraction`, `SkillInferenceOutput` |

## Cross-Service Data Access Rules
1. **No service writes to another service database.**
2. **Cross-service communication happens only through versioned APIs or domain events.**
3. **Read access across domains uses API composition, replicated read models, or event-fed projections; never foreign-table writes.**
4. **Ownership changes require schema migration plans and event-contract versioning before cutover.**

## Compatibility With Existing Repo Models
The ownership map aligns to the repository's core LMS entities (`User`, `Course`, `Lesson`, `Enrollment`, `Progress`, `Certificate`) and extends them with explicit bounded-context entities (`Institution`, `Program`, `Cohort`, `Session`, `Assessment`, `AttemptRecord`, `LearningEvent`, `AggregatedAnalytics`, AI artifacts).

## Security Isolation Requirements
- Each service has isolated credentials and least-privilege access limited to its own datastore.
- Database roles deny DML (INSERT/UPDATE/DELETE) into non-owned schemas.
- Service-to-service calls require authenticated service identity and scoped authorization.
- Event bus ACLs restrict publish/subscribe rights by owning domain.

## QC LOOP

### QC Pass 1 (Initial Evaluation)
- Data ownership clarity: **9/10**
- Absence of cross-domain writes: **10/10**
- Compatibility with repo models: **9/10**
- Security isolation: **9/10**

**Violations identified (score < 10):**
1. Naming mismatch risk between prompt terms (`Auth credentials`, `Attempt records`) and implementation-friendly canonical entity names.
2. Compatibility statement did not explicitly tie ownership map to repo core entity set.
3. Security controls did not explicitly include event-bus ACL boundaries.

**Corrections applied:**
1. Standardized canonical entity names (`AuthCredential`, `AttemptRecord`) while preserving required domain meaning.
2. Added explicit compatibility section tying map to repo core models.
3. Added event bus ACL requirement and explicit DML-deny control for non-owned schemas.

### QC Pass 2 (Post-Correction Re-evaluation)
- Data ownership clarity: **10/10**
- Absence of cross-domain writes: **10/10**
- Compatibility with repo models: **10/10**
- Security isolation: **10/10**

**Result:** QC target achieved at **10/10** across all categories.
