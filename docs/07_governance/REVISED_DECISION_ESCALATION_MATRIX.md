# REVISED_DECISION_ESCALATION_MATRIX

Status: Active
Authority Level: Critical
Last Reviewed: 2026-06-22
Owner: Shared

Supersedes: DECISION_ESCALATION_MATRIX.md (2026-06-21 version)
Change: SAFE_REPOSITORY_HYGIENE tier added between AUTONOMOUS and REQUIRES_APPROVAL
Policy: SAFE_REPOSITORY_HYGIENE_POLICY.md

---

## Purpose

This matrix defines what actions an AI session (or any developer) may take autonomously, what qualifies as safe repository hygiene, what requires owner approval, and what is prohibited. Classifications are based on actual project architecture and known risk areas.

---

## AUTONOMOUS

Actions that may be performed without owner approval. Reversible, low-risk, no external impact.

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

## SAFE_REPOSITORY_HYGIENE

Actions that improve repository organization, discoverability, documentation quality, and governance cleanliness — without modifying business logic, APIs, database structures, runtime behavior, infrastructure, deployment, or security boundaries. See SAFE_REPOSITORY_HYGIENE_POLICY.md for the full definition and hard boundaries.

**Execution rule:** An SRH action may be executed without owner approval in the current session, provided it has been explicitly classified as SRH in a governance audit or reclassification report. When uncertain, escalate.

### Documentation Organization
- Moving .md files between docs/ subdirectories (excluding docs/anchors/)
- Adding DEPRECATED, SUPERSEDED, HISTORICAL, or LEGACY banners to documents
- Updating document Status, Authority Level, or Owner metadata fields
- Adding cross-reference notes that point to authoritative documents
- Consolidating duplicate historical reports into a single archive entry
- Retiring documents to docs/_archive/ or workspace/archive/

### File and Folder Orientation
- Adding README.md files to any directory that lacks orientation documentation
- Adding PLACEHOLDER.md files to reserved-but-empty directories
- Adding classification comments to scripts or configs (comments only — no logic change)

### Governance and Reporting
- Creating new governance reports, audit outputs, and classification matrices in docs/08_reports/
- Updating classification matrices (DOCUMENT_INVENTORY.md, DOCUMENT_CLASSIFICATION_MATRIX.md)
- Adding entries to ARCHITECTURAL_GAP_REGISTER.md
- Generating or regenerating docs/07_governance/ documents that describe governance state

### Repository Cleanliness
- Adding entries to .gitignore for artifact types already excluded by convention (.pyc, .pytest_cache, node_modules)
- Moving non-production validation/QC scripts to the correct directory (e.g., docs/qc/*.py → validation/)
- Archiving outdated generated artifacts that have a confirmed replacement

### Boundary Conditions — Not SRH
- Any action touching docs/anchors/*.md → REQUIRES_APPROVAL
- Any action touching shared/models/, integrations/payments/, integrations/communication/ → REQUIRES_APPROVAL
- Any action touching service-manifest.json or event_topics.json → REQUIRES_APPROVAL
- Any action that deletes a file (even a generated artifact) → REQUIRES_APPROVAL
- Any action that changes .py logic, not just placement → REQUIRES_APPROVAL

---

## REQUIRES_APPROVAL

Actions that may only be performed with explicit owner approval in the current session.

### Schema and Data Model Changes
- Adding, renaming, or removing fields in shared/models/
- Changing the canonical tenant contract (docs/anchors/tenant-contract.md)
- Changing the event envelope structure (docs/anchors/event-envelope.md)
- Modifying database migration files in any service

### Anchor Updates
- Updating docs/anchors/capability-resolution.md (protected anchor)
- Updating docs/anchors/doc-precedence.md (protected anchor)
- Modifying any other docs/anchors/*.md file

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
- Moving integrations/payments/ or integrations/communication/ files

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
- Classifying root services/ as Active or Legacy (requires import analysis confirmation)
- Classifying root integrations/ relationship to backend/integrations/
- Classifying root shared/ import dependency relationship

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
| docs/anchors/ updates | REQUIRES_APPROVAL | Canonical contracts; changes cascade to all consumers |
| Test additions | AUTONOMOUS | Low risk; purely additive; no external impact |
| Documentation updates | AUTONOMOUS | Trivially reversible; no runtime impact |
| README additions | SAFE_REPOSITORY_HYGIENE | Orientation docs; no authority claims; reversible |
| Doc banner additions | SAFE_REPOSITORY_HYGIENE | Status metadata; no logic change; reversible |
| Moving docs .md files | SAFE_REPOSITORY_HYGIENE | Content unchanged; placement improved; reversible |
| Moving QC/validation scripts | SAFE_REPOSITORY_HYGIENE | Non-production tools; no runtime impact; reversible |
| .gitignore additions for artifacts | SAFE_REPOSITORY_HYGIENE | Excludes already-excluded artifact types; non-destructive |
| Root services/ classification | REQUIRES_APPROVAL | Owner must confirm import dependencies before any change |
| Safe code refactors | AUTONOMOUS only for R-010, path fixes | All others REQUIRES_APPROVAL |
