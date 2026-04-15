# Certificate Service (Enterprise LMS V2)

Production-ready `certificate_service` aligned to the existing Rails LMS `Certificate` runtime model.

## Service module structure

- `app/main.py` — versioned REST API routes (`/api/v1/...`), tenant context dependency, health/metrics.
- `app/schemas.py` — request/response contracts.
- `app/models.py` — domain entities (`Certificate`, `CertificateTemplate`, `VerificationMetadata`, `CompletionRef`, `BadgeExtensionProfile`).
- `app/service.py` — issuance workflow, lifecycle rules, audit logging integration, observability hooks, lifecycle events.
- `app/store.py` — storage contract (`CertificateStore`) + in-memory adapter.
- `src/audit.py` — audit event model and logger.
- `migrations/0001_create_certificates.sql` — baseline schema for certificate entity.

## API routes

- `POST /api/v1/certificates`
- `GET /api/v1/certificates/{certificate_id}`
- `POST /api/v1/certificates/{certificate_id}/revoke`
- `GET /api/v1/certificates/verify/{verification_code}` (public)
- `POST /api/v1/certificate-templates`
- `PATCH /api/v1/certificate-templates/{template_id}`
- `GET /api/v1/certificate-templates/{template_id}`
- `POST /api/v1/certificates/{certificate_id}/badge-extension`
- `GET /health`
- `GET /metrics`

## Ownership boundaries

- Certificate is the core runtime credential entity.
- Completion linkage is via `completion_ref` provenance only.
- Assessment ownership remains external.
- Progress ownership remains external.
- No shared database writes; this service owns only its storage contract.

## Events published

- `lms.certificate.issued.v1`
- `lms.certificate.revoked.v1`
- `lms.certificate.expired.v1`
- `lms.certificate.template_created.v1`
- `lms.certificate.template_updated.v1`
- `lms.certificate.badge_extension_attached.v1`

## Migration notes

1. Reuse existing Rails `certificates` field semantics (`verification_code`, tenant/user/course uniqueness behavior, lifecycle fields).
2. Keep existing verification URLs stable by preserving `verification_code` as externally resolvable identifier.
3. Run service storage migration independently; do not write into assessment or progress databases.
4. Configure JWT secret (`JWT_SHARED_SECRET`) and tenant propagation header (`X-Tenant-Id`) at gateway level.

## Tests

```bash
python -m unittest backend/services/certificate-service/tests/test_certificate_service.py
python -m unittest backend/services/certificate-service/tests/test_audit_logging.py
```
