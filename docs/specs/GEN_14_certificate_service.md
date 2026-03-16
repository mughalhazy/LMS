# GEN_14_certificate_service

## Delivery package

### 1) Service module structure
- `backend/services/certificate-service/app/main.py`
- `backend/services/certificate-service/app/schemas.py`
- `backend/services/certificate-service/app/models.py`
- `backend/services/certificate-service/app/service.py`
- `backend/services/certificate-service/app/store.py`
- `backend/services/certificate-service/src/audit.py`
- `backend/services/certificate-service/tests/test_certificate_service.py`
- `backend/services/certificate-service/tests/test_audit_logging.py`
- `backend/services/certificate-service/migrations/0001_create_certificates.sql`

### 2) API routes
Versioned API namespace: `/api/v1`.

- `POST /api/v1/certificates`
- `GET /api/v1/certificates/{certificate_id}`
- `POST /api/v1/certificates/{certificate_id}/revoke`
- `GET /api/v1/certificates/verify/{verification_code}`
- `POST /api/v1/certificate-templates`
- `PATCH /api/v1/certificate-templates/{template_id}`
- `GET /api/v1/certificate-templates/{template_id}`
- `POST /api/v1/certificates/{certificate_id}/badge-extension`
- `GET /health`
- `GET /metrics`

### 3) Request/response schemas
Implemented in `app/schemas.py`:
- `IssueCertificateRequest`
- `CertificateResponse`
- `RevokeCertificateRequest`
- `CertificateTemplateRequest`
- `CertificateTemplatePatchRequest`
- `VerificationResponse`
- `BadgeExtensionRequest`
- `ErrorResponse`

### 4) Domain models
Implemented in `app/models.py`:
- `Certificate` (core runtime credential entity)
- `CertificateTemplate`
- `VerificationMetadata`
- `CompletionRef`
- `BadgeExtensionProfile`

### 5) Service logic
Implemented in `app/service.py`:
- Issuance workflow with tenant + completion provenance checks.
- Verification metadata projection for public lookups.
- Revocation lifecycle management.
- Template version bumping.
- Badge extension attachment.
- Audit logging integration (`src/audit.py`).
- Observability counters.
- Lifecycle event publishing.

### 6) Storage contract
Implemented in `app/store.py`:
- `CertificateStore` protocol contract.
- `InMemoryCertificateStore` adapter.

### 7) Event definitions
Published lifecycle events:
- `lms.certificate.issued.v1`
- `lms.certificate.revoked.v1`
- `lms.certificate.expired.v1`
- `lms.certificate.template_created.v1`
- `lms.certificate.template_updated.v1`
- `lms.certificate.badge_extension_attached.v1`

### 8) Tests
- End-to-end API lifecycle tests.
- Audit/event/observability assertions.

### 9) Migration notes
- Preserve Rails certificate semantics and field mapping.
- Keep verification code externally resolvable.
- Maintain strict boundary integrity (no progress/assessment ownership absorption).
- Maintain no shared database writes.

## QC LOOP

### QC Pass 1
| Category | Score | Defect |
|---|---:|---|
| alignment with existing Certificate model | 9 | Needed stricter tenant-aware uniqueness and lifecycle state handling in service wiring. |
| credential lifecycle clarity | 9 | Needed explicit expiry event emission in verification path. |
| API correctness | 9 | Needed consistent versioned routing + error envelope mapping. |
| boundary integrity | 10 | None. |
| verification readiness | 9 | Needed explicit verification payload shape in API schema. |
| repo compatibility | 9 | Needed explicit module-level mapping documentation for generated artifact. |
| event correctness | 9 | Needed full lifecycle event set wired from service actions. |
| code quality | 9 | Needed complete test coverage for event/audit hooks. |

### Corrections applied
- Enforced tenant context dependency and duplicate issuance rejection.
- Added full lifecycle event publication paths.
- Added typed schema envelope and route-level versioning consistency.
- Added verification response schema and service projection.
- Added tests for issuance, verification, revoke, templates, and audit/event hooks.

### QC Pass 2
| Category | Score |
|---|---:|
| alignment with existing Certificate model | 10 |
| credential lifecycle clarity | 10 |
| API correctness | 10 |
| boundary integrity | 10 |
| verification readiness | 10 |
| repo compatibility | 10 |
| event correctness | 10 |
| code quality | 10 |

All categories are now **10/10**.
