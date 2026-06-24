# audit-policy-service

Independent audit logging and policy enforcement layer. Evaluates policy decisions (ALLOW/DENY/CHALLENGE/REQUIRE_JIT_APPROVAL), ingests canonical audit events into a hash-chained immutable ledger, manages retention and legal holds, and exports RBAC-gated signed compliance evidence. Design: `docs/designs/audit-policy-layer-design.md` (B2P07).

## Canonical audit event families (B2P07 taxonomy)

`capability.access.*` | `config.change.*` | `entitlement.change.*` | `policy.*` | `audit.export.*` | `audit.legal_hold.*` | `audit.retention.*`

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/policy/evaluate` | Evaluate policy decision |
| POST | `/api/v1/policy/evaluate-batch` | Batch policy evaluation |
| POST | `/api/v1/policy/bundles` | Publish policy bundle (signature-verified — B15-003) |
| POST | `/api/v1/audit/events` | Ingest audit event |
| GET | `/api/v1/audit/records` | Query audit records |
| GET | `/api/v1/audit/export` | Export compliance evidence — RBAC-gated + signed manifest (B15-004) |
| GET | `/api/v1/audit/taxonomy` | Get versioned event taxonomy (B15-002) |
| POST | `/api/v1/audit/taxonomy/event-types` | Register new event type (B15-002) |
| POST | `/api/v1/audit/retention/legal-hold` | Set legal hold on records (B15-001) |
| POST | `/api/v1/audit/retention/class` | Apply retention class 1y/3y/7y (B15-001) |
| GET | `/health` | Health check |

## B15 fixes (2026-06-02)

- **B15-001**: `RetentionAndLegalHoldManager` — legal hold flag on records; retention classes (standard 1y / regulatory 3y / legal 7y); legal hold supersedes expiry
- **B15-002**: `AuditTaxonomyManager` — versioned taxonomy; `GET /api/v1/audit/taxonomy`; `POST /audit/taxonomy/event-types` to extend without semantic drift
- **B15-003**: `PolicyRegistryPort` — `publish_bundle_verified()` validates HMAC signature of bundle before activation; rejects on mismatch
- **B15-004**: `export_evidence_verified()` — RBAC gate (auditor/compliance_officer/legal_counsel); export access logged as immutable audit event; watermark_id + signed_manifest in response

## Gateway

Route: `/api/v1/audit`, `/api/v1/policy` | Rate limit: `internal-control-plane`
