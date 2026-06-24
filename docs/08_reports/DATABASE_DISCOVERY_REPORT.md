# DATABASE_DISCOVERY_REPORT

Status: Active
Authority Level: Medium
Last Reviewed: 2026-06-23
Owner: AI
Phase: Phase 2 — Backend Authority Capture

Source: Direct code inspection of backend/services/

---

## Purpose

Detailed findings from the database layer discovery performed during Phase 2. Documents exactly what was found — no recommendations, no redesign.

---

## Summary Finding (Updated 2026-06-23)

**Original finding (Phase 2)**: All services used in-memory storage. **Now corrected**: 16 services use SQLite persistence via complete store_db.py implementations wired in Task 7. 53 services remain in-memory.

---

## Evidence: In-Memory Store Pattern

Pattern confirmed in every inspected service:

| Service | Store Class | Location | Pattern |
|---|---|---|---|
| auth-service | `InMemoryAuthStore` | `backend/services/auth-service/app/store.py` | Dict |
| rbac-service | `InMemoryRBACStore` | `backend/services/rbac-service/app/store.py` | Dict |
| tenant-service | `InMemoryTenantStore` | `backend/services/tenant-service/app/repository.py` | Dict |
| progress-service | `InMemoryProgressStore`, `InMemoryIdempotencyStore` | `backend/services/progress-service/app/store.py` | Dict |
| enrollment-service | `InMemoryEnrollmentStore`, `InMemoryAuditLogStore` | `backend/services/enrollment-service/app/store.py` | Dict |
| checkout-service | `InMemoryCheckoutStore` | `backend/services/checkout-service/app/store.py` | Dict |

All `backend/services/` were assumed to follow the same pattern based on consistent naming conventions across the codebase (`InMemoryXStore` in every `store.py`).

---

## store_db.py Files (Updated 2026-06-23)

`store_db.py` files are complete SQLite implementations using `backend/services/shared/db/engine.py` `BaseRepository`. They are NOT stubs and do NOT use SQLAlchemy/asyncpg/psycopg2. They use Python stdlib `sqlite3` directly.

**16 services actively import and use store_db.py** (wired in Task 7): auth, rbac, enrollment, progress, tenant, assessment, certificate, lesson, program, badge, session, user, org, cohort, institution, course.

Prior characterization as "never imported" was incorrect — corrected 2026-06-23.

---

## What the Specs Describe

Engineering specs describe persistent entities. Example from `docs/specs/auth-service-spec.md` §3:

| Spec Entity | Purpose | Implementation Reality |
|---|---|---|
| `auth_identity` | Stores password hashes per user per tenant | `UserCredential` dataclass in-memory |
| `session` | Active session state | `Session` dataclass in-memory |
| `refresh_token_family` | Refresh token rotation families | Not found in implementation |
| `refresh_token` | Individual refresh tokens | Not as separate model |
| `password_reset_challenge` | One-time reset tokens | `ResetChallenge` dataclass in-memory |
| `login_audit_event` | Append-only audit trail | Not found as separate store |
| `key_metadata` | RSA key rotation metadata | Module-level `_RSA_KEY_CACHE` variable |

All spec entities map to in-memory data structures, not database tables.

---

## Data Retention Policy (From Spec — Not Implemented)

auth-service-spec.md §3 specifies data retention:
- sessions: 90 days after expiry/revocation
- password_reset_challenge: 30 days after completion
- login_audit_event: 400 days (compliance)

**Reality**: No data retention policy is enforceable with in-memory storage — data evicts on restart.

---

## Idempotency Storage

Two idempotency stores identified:

| Service | Store Class | Notes |
|---|---|---|
| progress-service | `InMemoryIdempotencyStore` | Prevents duplicate progress writes |
| checkout-service | Inline idempotency in `CheckoutService.submit_session()` | Prevents duplicate submissions |

Both are in-memory and lose state on restart.

---

## What Was Not Found

| Expected | Result |
|---|---|
| SQLAlchemy, asyncpg, psycopg2 imports | Not found in any inspected main.py |
| DATABASE_URL, POSTGRES_URI, REDIS_URL env var references | Not found in any inspected main.py |
| Alembic or database migration files | Not found |
| ORM model declarations (SQLAlchemy Base, Pydantic ORM mode) | Not found |
| Connection pooling configuration | Not found |
| Redis client imports | Not found in any inspected main.py |
| Database health check in /health endpoint | Not found — health returns `{"status": "ok"}` without DB check |

---

## Inspection Scope

Services directly inspected:
- auth-service (main.py, models.py, store.py, security.py)
- rbac-service (main.py, models.py, security.py)
- tenant-service (main.py)
- progress-service (main.py)
- enrollment-service (main.py)
- checkout-service (main.py)

Services inferred from pattern:
- All other 59 Python services assumed to follow same `InMemoryXStore` pattern
- Node.js services (prerequisite-engine, scorm) not inspected

---

## Questions for Owner

| ID | Question |
|---|---|
| D-001 | Does checkout-service have persistence for orders/sessions anywhere in its implementation (e.g., store_db.py or external call)? |
| Q-DB-001 | Is there a deployment mechanism (init script, seed script) that pre-loads data into services before they start? |
| Q-DB-002 | Are any store_db.py files actively used in staging/production? |
| Q-DB-003 | Is there an external persistence layer (managed DB service) that services call via HTTP? |

---

## Related Documents

- `docs/01_backend/DATABASE_SCHEMA.md` — data model documentation
- `docs/08_reports/BACKEND_GAP_REGISTER.md` — GAP-002 (no persistent database)
- `docs/08_reports/BACKEND_RISK_REGISTER.md` — RISK-001, RISK-002, RISK-003
- `docs/specs/auth-service-spec.md` §3 — spec-level data model
