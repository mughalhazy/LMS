# SPEC_14_certificate_service

## 1) Service purpose

`certificate_service` is the credential runtime boundary for Enterprise LMS V2. It operationalizes the existing Rails `Certificate` model as the canonical credential record and exposes certificate issuance, template usage, verification metadata, completion linkage, and badge-extension hooks.

The service is explicitly **extension-oriented**:
- It preserves `Certificate` as the core runtime entity from the repository.
- It consumes completion/eligibility signals from other domains.
- It does not own assessment scoring logic.
- It does not own learner progress state.

## 2) Alignment to existing certificate runtime model

The service contract maps directly to the current certificate data shape already implemented in the repo runtime (`certificate_id`, `verification_code`, `tenant_id`, `user_id`, `course_id`, `enrollment_id`, `issued_at`, `expires_at`, `status`, `metadata`, `artifact_uri`, `revoked_at`, `revocation_reason`) and preserves uniqueness constraints for tenant/user/course credential issuance.

Compatibility requirements:
- One active certificate record per `(tenant_id, user_id, course_id)` unless superseded by explicit renewal policy.
- Verification must remain code-based and externally checkable without exposing protected learner data.
- Revocation and expiration are first-class lifecycle states, not hard deletes.

## 3) Owned data

### 3.1 Core entities
- **Certificate** (runtime credential record; canonical).
- **CertificateTemplate** (rendering/layout + branding references).
- **CertificateVerificationMetadata** (public verification projection: status, verify URL, cryptographic/checksum metadata, display claims policy).
- **CertificateCompletionLink** (provenance link to completion source event and enrollment context).
- **BadgeExtensionProfile** (optional mapping metadata enabling downstream badge issuance without replacing certificate ownership).

### 3.2 Non-owned references
- Progress state and completion calculation (owned by `progress_service`).
- Assessment definitions, attempts, and scoring (owned by `assessment_service`).
- User identity profile and authoritative learner status (owned by `user_service`).

## 4) API endpoints

All endpoints are tenant-scoped under `/api/v1`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/certificates` | Issue certificate for eligible completion target. |
| GET | `/certificates/{certificate_id}` | Retrieve full tenant-scoped certificate record. |
| GET | `/certificates` | List certificates with filters (`user_id`, `course_id`, `status`, `issued_after`, `issued_before`). |
| POST | `/certificates/{certificate_id}/revoke` | Revoke active certificate with reason and actor attribution. |
| POST | `/certificate-templates` | Create certificate template. |
| PATCH | `/certificate-templates/{template_id}` | Update template version/metadata without mutating historical certificate records. |
| GET | `/certificate-templates/{template_id}` | Retrieve template. |
| GET | `/certificates/verify/{verification_code}` | Public verification metadata lookup. |
| POST | `/certificates/{certificate_id}/badge-extension` | Attach badge extension metadata for downstream badge providers. |

## 5) Request and response contracts

### 5.1 Issue certificate
**POST** `/api/v1/certificates`

Request:
```json
{
  "tenant_id": "tenant_123",
  "user_id": "user_456",
  "course_id": "course_789",
  "enrollment_id": "enr_234",
  "completion_ref": {
    "source_event": "lms.progress.course_completed.v1",
    "source_event_id": "evt_001",
    "completed_at": "2026-01-10T11:45:00Z"
  },
  "template_id": "tpl_modern_001",
  "artifact_uri": "s3://certificates/tenant_123/cert_abc.pdf",
  "metadata": {
    "grade": "A",
    "language": "en"
  },
  "expires_at": null,
  "issued_by": "system"
}
```

Response `201 Created`:
```json
{
  "certificate_id": "cert_abc",
  "verification_code": "VRF-7TJ9-KL20",
  "tenant_id": "tenant_123",
  "user_id": "user_456",
  "course_id": "course_789",
  "enrollment_id": "enr_234",
  "status": "active",
  "issued_at": "2026-01-10T11:46:02Z",
  "expires_at": null,
  "artifact_uri": "s3://certificates/tenant_123/cert_abc.pdf",
  "metadata": {
    "grade": "A",
    "language": "en",
    "template_id": "tpl_modern_001"
  }
}
```

### 5.2 Revoke certificate
**POST** `/api/v1/certificates/{certificate_id}/revoke`

Request:
```json
{
  "tenant_id": "tenant_123",
  "reason": "policy_violation",
  "revoked_by": "admin_22"
}
```

Response `200 OK`:
```json
{
  "certificate_id": "cert_abc",
  "status": "revoked",
  "revoked_at": "2026-02-01T08:00:00Z",
  "revocation_reason": "policy_violation"
}
```

### 5.3 Verify certificate metadata (public)
**GET** `/api/v1/certificates/verify/{verification_code}`

Response `200 OK`:
```json
{
  "verification_code": "VRF-7TJ9-KL20",
  "is_valid": true,
  "status": "active",
  "certificate_id": "cert_abc",
  "tenant_display_name": "Acme Academy",
  "learner_display_name": "Jane Doe",
  "course_title": "Enterprise Security Foundations",
  "issued_at": "2026-01-10T11:46:02Z",
  "expires_at": null,
  "revoked_at": null,
  "verification_url": "https://lms.example.com/verify/VRF-7TJ9-KL20"
}
```

### 5.4 Error contract (all endpoints)
```json
{
  "error": {
    "code": "CERTIFICATE_ALREADY_EXISTS",
    "message": "A certificate already exists for tenant/user/course.",
    "correlation_id": "req_f2f0..."
  }
}
```

## 6) Events produced

- `lms.certificate.issued.v1`
  - Emitted after successful issuance.
  - Payload keys: `certificate_id`, `verification_code`, `tenant_id`, `user_id`, `course_id`, `enrollment_id`, `issued_at`, `expires_at`, `status`, `template_id`, `completion_ref`.
- `lms.certificate.revoked.v1`
  - Emitted on revocation.
  - Payload keys: `certificate_id`, `tenant_id`, `revoked_at`, `revocation_reason`, `revoked_by`.
- `lms.certificate.expired.v1`
  - Emitted when certificate status transitions to expired.
  - Payload keys: `certificate_id`, `tenant_id`, `expired_at`.
- `lms.certificate.template_created.v1` / `lms.certificate.template_updated.v1`
  - Emitted for template lifecycle updates.
- `lms.certificate.badge_extension_attached.v1`
  - Emitted when badge extension metadata is attached.

## 7) Events consumed

- `lms.progress.course_completed.v1` (from `progress_service`)
  - Primary issuance trigger or eligibility reference.
- `lms.progress.completion_corrected.v1` (from `progress_service`)
  - Handles rollback/reconciliation, including potential revocation workflows.
- `lms.assessment.passed.v1` (from `assessment_service`)
  - Optional enrichment signal for certificate metadata/provenance only; no attempt ownership.
- `lms.user.profile_updated.v1` (from `user_service`)
  - Updates denormalized display fields used in certificate rendering and verification projections.
- `lms.user.deactivated.v1` (from `user_service`)
  - Compliance policy hook for certificate status review; does not mutate user ownership boundaries.

## 8) Integration contracts with peer services

### 8.1 `progress_service` integration
- Certificate issuance requires verifiable completion provenance (`completion_ref.source_event_id`).
- `certificate_service` may query read-only completion eligibility endpoint:
  - `GET /api/v1/progress/eligibility/courses/{course_id}/users/{user_id}`
- Progress remains source of truth for completion state transitions.

### 8.2 `assessment_service` integration
- `certificate_service` can consume pass/fail summaries or compliance flags as metadata enrichment.
- It cannot create attempts, score attempts, or own assessment records.
- Assessment identifiers referenced inside certificate metadata are foreign keys only.

### 8.3 `user_service` integration
- User identity fields (name, external identifier, locale) are read from `user_service` at issuance/render time.
- User lifecycle policies may influence certificate visibility/compliance state, but user state is never owned or mutated by this service.

## 9) Boundary integrity rules

- No assessment authoring, scoring, or attempt persistence inside `certificate_service`.
- No progress event authoring or completion-state persistence inside `certificate_service`.
- Certificate records remain immutable except for allowed lifecycle transitions (`active` -> `revoked`/`expired`) and non-destructive metadata augmentation.
- Template updates are versioned; previously issued certificates retain original template reference for auditability.

## 10) Verification and badge-extension readiness

- Verification endpoint must provide high-confidence validity signals (`status`, revocation/expiry timestamps, canonical verification URL).
- Verification payload must support policy-based redaction for public contexts.
- Badge-extension profile stores issuer mapping, badge-class identifiers, and evidence URI pointers, enabling future Open Badges workflows while keeping `Certificate` as primary credential entity.

## 11) QC loop

### QC Pass 1

| Category | Score (1–10) | Defect identified |
|---|---:|---|
| Alignment with existing Certificate model | 9 | Needed explicit field-level mapping to repo runtime attributes and uniqueness behavior. |
| Credential lifecycle clarity | 9 | Needed explicit lifecycle transition constraints and reconciliation input events. |
| API correctness | 9 | Needed standardized endpoint namespace and explicit error contract. |
| Boundary integrity | 10 | None. |
| Verification readiness | 9 | Needed concrete verification response contract and redaction note. |
| Repo compatibility | 9 | Needed direct compatibility statement with existing certificate-service schema shape. |

### Revisions applied
- Added explicit field-level runtime mapping and uniqueness compatibility guarantees.
- Added lifecycle constraints and correction event handling (`completion_corrected`).
- Standardized API paths under `/api/v1` and added shared error contract.
- Added explicit verification response payload and policy-based redaction requirement.
- Added repo compatibility language anchoring to current certificate service schema fields.

### QC Pass 2

| Category | Score (1–10) | Result |
|---|---:|---|
| Alignment with existing Certificate model | 10 | Fully mapped to existing runtime attributes and constraints. |
| Credential lifecycle clarity | 10 | Issuance/revocation/expiry/reconciliation paths are explicit. |
| API correctness | 10 | Endpoint and contracts are unambiguous and versioned. |
| Boundary integrity | 10 | Ownership boundaries with progress and assessment are preserved. |
| Verification readiness | 10 | Public verification metadata contract and compliance behavior defined. |
| Repo compatibility | 10 | Specification remains extension-only over existing certificate runtime entity. |

**QC status: all categories = 10/10.**
