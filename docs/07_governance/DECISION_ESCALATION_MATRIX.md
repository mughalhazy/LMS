# DECISION_ESCALATION_MATRIX

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-22
Owner: Human

> **REVISED** — A `SAFE_REPOSITORY_HYGIENE` tier has been added between AUTONOMOUS and REQUIRES_APPROVAL.
> See: docs/07_governance/REVISED_DECISION_ESCALATION_MATRIX.md (complete updated matrix)
> See: docs/07_governance/SAFE_REPOSITORY_HYGIENE_POLICY.md (SRH definition and hard boundaries)
> This document is retained as the original baseline. The REVISED version is the active authority.

---

## Purpose

This matrix defines what actions an AI session (or any developer) may take autonomously, what requires owner approval, and what is prohibited. Classifications are based on actual project architecture and known risk areas.

---

## AUTONOMOUS

Actions that may be performed without owner approval. These are reversible, low-risk, and have no external impact.

### Documentation
- Updating docs/specs/ with verified information extracted from code
- Creating new docs/00_authority/, docs/06_decisions/, docs/07_governance/, docs/08_reports/ files
- Fixing typos, formatting, broken links, stale paths in documentation
- Adding TBD markers for unverified content
- Updating doc-catalogue.md with new file entries

### Testing
- Adding new pytest test files to backend/services/*/tests/
- Adding new pytest test files to services/*/tests/
- Fixing broken tests that were caused by safe code changes
- Running existing test suites

### Safe Code Refactors
- Adding `if parent not in sys.path:` guard to `_load_module()` functions (R-010)
- Adding `if module_name in sys.modules: return sys.modules[module_name]` guard to `_load_module()`
- Fixing `python` → `py -3` in any script or documentation
- Replacing hard-coded D:\LMS paths with correct D:\SaaS\LMS paths

### Workspace Operations
- Creating new files in workspace/sessions/
- Reading any file in the repository
- Running validation commands that do not modify files
- Moving prompt files to workspace/sessions/ session directories

---

## REQUIRES_APPROVAL

Actions that may only be performed with explicit owner approval in the current session.

### Schema and Data Model Changes
- Adding, renaming, or removing fields in shared/models/
- Changing the canonical tenant contract (docs/anchors/tenant-contract.md)
- Changing the event envelope structure (docs/anchors/event-envelope.md)
- Modifying database migration files in any service

### Authentication and Security
- Changing JWT algorithm from RS256 to any other algorithm (including HS256 "fixes")
- Changing the RS256 → HS256 remediation approach for notification, subscription, catalog services
- Modifying RBAC permission definitions
- Changing CORS configuration
- Changing rate limiting rules
- Adding or removing API key validation

### Architecture Changes
- Implementing R-001 (entitlement-service DI) — requires explicit "implement R-001" instruction
- Implementing R-003 (system-of-record DI) — requires explicit "implement R-003" instruction
- Implementing R-004 (circular import resolution) — requires explicit "implement R-004" instruction
- Moving files between services/ and backend/services/
- Creating or deleting service directories in backend/services/ or services/
- Changing the importlib composition pattern in any services/ module

### Service Manifest
- Adding or removing entries from service-manifest.json
- Changing the `app_module` field for any registered service

### Commerce and Payments
- Changing payment adapter logic in integrations/payments/
- Changing CheckoutService idempotency logic
- Changing reconciliation logic in services/commerce/reconciliation.py or integrations/payments/reconciliation.py
- Adding support for new payment providers
- Changing JazzCash/EasyPaisa adapter configuration

### External-Facing Contracts
- Changing any API route path (method + path string)
- Changing API response schema for any existing endpoint
- Changing event topic names in event_topics.json
- Changing event_type values in the event envelope

### Infrastructure
- Creating Dockerfiles or docker-compose.yml
- Creating CI/CD pipeline configuration
- Changing environment variable names or values
- Changing .npmrc, pyproject.toml, or other tooling configuration

### Owner Decision Items
- Any action that requires D-001 through D-005 from U11 to be answered first
- Implementing CheckoutService persistence (R-005) — owner must confirm persistence backend
- Deleting services/file-storage/ or services/interaction-service/ (R-006)
- Implementing class-based service startup documentation (R-009) — owner must confirm mechanism

---

## PROHIBITED

Actions that must never be performed regardless of instruction.

### Data Safety
- Deleting or truncating any database table or migration
- Removing or disabling audit logging in audit-policy-service or any service
- Removing or bypassing tenant_id isolation checks in any service
- Deleting production payment transaction records or reconciliation records

### Security
- Removing authentication middleware from any service
- Disabling JWT signature verification
- Hardcoding secrets, API keys, or passwords in source files
- Removing the idempotency check from CheckoutService.submit_session()

### Architecture Integrity
- Making the canonical event envelope have fewer than 7 required fields
- Making tenant_id optional in any service
- Removing the `capability → config → entitlement → final_state` evaluation order
- Adding runtime branching on country_code or segment_type in business logic (MS-CONFIG-01 violation)

### Workspace
- Writing any file to C: drive (workspace is sealed to D:)
- Deleting files from workspace/sessions/ (session history must be preserved)
- Deleting or overwriting docs/anchors/ files without creating a supersession record

---

## ESCALATION PROTOCOL

If an action is not clearly covered by the above categories:

1. State the action and which category it most resembles
2. State the risk if performed incorrectly
3. State the rollback plan
4. Ask the owner for approval before proceeding

**Default when uncertain:** Do not proceed. Ask.

---

## CLASSIFICATION RATIONALE

| Area | Classification | Reason |
|---|---|---|
| Tenant isolation | PROHIBITED to remove | Multi-tenant SaaS core constraint |
| Payment idempotency | PROHIBITED to remove | JazzCash webhooks may fire multiple times; duplicate charge risk |
| Config branching ban | PROHIBITED to violate | MS-CONFIG-01; breaks country layer architecture |
| HS256 → RS256 migration | REQUIRES_APPROVAL | Security change; affects 3 services; coordinated migration |
| shared/models/ changes | REQUIRES_APPROVAL | Cross-service contracts; changes cascade to all consumers |
| Test additions | AUTONOMOUS | Low risk; purely additive; no external impact |
| Documentation updates | AUTONOMOUS | Trivially reversible; no runtime impact |
| safe code refactors | AUTONOMOUS only for specific R-010, path fixes | All others REQUIRES_APPROVAL |
