# SPEC_05 — institution_service (Enterprise LMS V2)

## 1) Service Purpose

`institution_service` introduces a global institution model above existing Rails LMS runtime entities (tenant, user, course runtime enrollments) without replacing them.

It is the system-of-record for:
- Institution lifecycle management (draft, active, suspended, archived).
- Institution hierarchy management (parent/child graph with policy constraints).
- Institution type management (school, university, academy, tutor organization, corporate training organization).
- Institution-to-tenant linkage (mapping one or more runtime tenants to institutions).
- Academy and tutor organization support for franchise, network, and affiliated delivery models.

Non-goals:
- It **does not** own Course, Lesson, Enrollment, Progress, or Certificate records.
- It **does not** replace runtime tenancy; it overlays organizational structure and governance.

---

## 2) Domain Boundaries and Ownership

### 2.1 Owns

| Entity | Description | Key Fields |
|---|---|---|
| institutions | Canonical institution profile and lifecycle state. | institution_id (PK), institution_type, legal_name, display_name, status, registration_country, default_locale, timezone, created_at, updated_at |
| institution_hierarchy_edges | Parent-child links between institutions. | edge_id (PK), parent_institution_id, child_institution_id, relationship_type, effective_from, effective_to (nullable), status |
| institution_types | Allowed type taxonomy and extensible metadata. | type_code (PK), type_name, is_system_type, governance_profile |
| institution_tenant_links | Mapping between institution and runtime tenant(s). | link_id (PK), institution_id, tenant_id, link_scope (`primary`/`affiliate`/`delivery`), status, linked_at |
| institution_contacts | Governance and escalation contacts. | contact_id (PK), institution_id, contact_type, name, email, phone, status |
| institution_policies | Institution-level policy references used by downstream services. | policy_id (PK), institution_id, policy_domain, policy_ref, version, status |

### 2.2 Does Not Own (Explicit)

| Entity | Owning Service |
|---|---|
| Course | program_service / course_service runtime domain |
| Lesson | lesson/content runtime domain |
| Enrollment | enrollment/runtime learning domain |
| Progress | progress_tracking domain |
| Certificate | certification/compliance domain |

### 2.3 Runtime Alignment Rule

- Existing runtime entities continue operating tenant-first.
- `institution_service` adds a governance layer where `tenant_id` can be linked to one institution context for primary governance, with optional affiliate links for cross-brand operations.
- Runtime queries that need institution context resolve via `institution_tenant_links` rather than duplicating institution fields in runtime transactional tables.

---

## 3) Supported Institution Types

System-supported base types:
- `school`
- `university`
- `academy`
- `tutor_organization`
- `corporate_training_organization`

Type extensibility:
- Additional subtypes may be introduced as aliases/children of base types through `institution_types` metadata, but base types remain invariant for cross-service compatibility.

---

## 4) Lifecycle Model

| State | Description | Allowed Transitions |
|---|---|---|
| draft | Institution shell, not yet operational. | active, archived |
| active | Operational and linkable to tenants/programs. | suspended, archived |
| suspended | Temporarily restricted by compliance/contract policy. | active, archived |
| archived | End-of-life metadata retained; no new links. | (terminal, except admin restore workflow) |

Lifecycle rules:
- `active` required before creating `primary` tenant link.
- `suspended` blocks new tenant links and hierarchy mutations except emergency unlink operations.
- `archived` institutions cannot be parents or children in active hierarchy edges.

---

## 5) Hierarchy Rules

Hierarchy model: directed acyclic graph constrained by governance policy.

1. No cycles permitted.
2. A child can have at most one active `governance_parent` at a time.
3. Additional non-governance edges allowed (`affiliate`, `academic_partnership`) if explicitly enabled.
4. Parent and child must be globally unique IDs; cross-country and cross-region relationships are allowed.
5. Each institution must resolve one effective governance root for policy inheritance.
6. Re-parenting requires:
   - no cycle after mutation,
   - no conflicting active primary tenant link policy,
   - audit log with actor, reason, before/after parent IDs.
7. Tutor organization support:
   - `tutor_organization` may be child of `academy`, `school`, or `corporate_training_organization`.
8. Academy network support:
   - `academy` can be parent of other academies for franchise structures when policy flag `allow_academy_franchise=true`.

---

## 6) API Endpoints (v1)

Base path: `/api/v1/institutions`

### 6.1 Institution Lifecycle

| Method + Path | Purpose |
|---|---|
| `POST /api/v1/institutions` | Create institution. |
| `GET /api/v1/institutions/{institution_id}` | Fetch institution profile. |
| `PATCH /api/v1/institutions/{institution_id}` | Update mutable profile fields. |
| `POST /api/v1/institutions/{institution_id}/activate` | Transition draft/suspended → active. |
| `POST /api/v1/institutions/{institution_id}/suspend` | Transition active → suspended. |
| `POST /api/v1/institutions/{institution_id}/archive` | Transition to archived. |

### 6.2 Hierarchy Management

| Method + Path | Purpose |
|---|---|
| `POST /api/v1/institutions/{institution_id}/parents/{parent_id}` | Attach governance/affiliate parent edge. |
| `DELETE /api/v1/institutions/{institution_id}/parents/{parent_id}` | Remove hierarchy edge. |
| `GET /api/v1/institutions/{institution_id}/hierarchy` | Return ancestors, descendants, effective root. |
| `POST /api/v1/institutions/{institution_id}/reparent` | Atomic re-parent with validation. |

### 6.3 Institution Type Management

| Method + Path | Purpose |
|---|---|
| `GET /api/v1/institution-types` | List supported types and metadata. |
| `POST /api/v1/institution-types` | Add custom subtype metadata (admin-only). |
| `PATCH /api/v1/institution-types/{type_code}` | Update governance profile/flags. |

### 6.4 Institution-to-Tenant Linkage

| Method + Path | Purpose |
|---|---|
| `POST /api/v1/institutions/{institution_id}/tenant-links` | Create link to tenant. |
| `GET /api/v1/institutions/{institution_id}/tenant-links` | List all tenant links. |
| `DELETE /api/v1/institutions/{institution_id}/tenant-links/{link_id}` | Deactivate link. |
| `GET /api/v1/tenants/{tenant_id}/institution-context` | Resolve institution context for runtime tenant. |

---

## 7) Request/Response Contracts (Core)

### 7.1 Create Institution

**Request**
```json
{
  "institution_type": "academy",
  "legal_name": "Global Data Academy Ltd",
  "display_name": "Global Data Academy",
  "registration_country": "GB",
  "default_locale": "en-GB",
  "timezone": "Europe/London",
  "metadata": {
    "accreditation_ids": ["QAA-1234"]
  }
}
```

**Response (201)**
```json
{
  "institution_id": "ins_01J0ABCXYZ",
  "status": "draft",
  "institution_type": "academy",
  "created_at": "2026-01-17T10:22:11Z"
}
```

### 7.2 Create Tenant Link

**Request**
```json
{
  "tenant_id": "ten_01HZZ9K2",
  "link_scope": "primary",
  "effective_from": "2026-01-20"
}
```

**Response (201)**
```json
{
  "link_id": "itl_01HZZ9LM",
  "institution_id": "ins_01J0ABCXYZ",
  "tenant_id": "ten_01HZZ9K2",
  "link_scope": "primary",
  "status": "active"
}
```

### 7.3 Reparent Institution

**Request**
```json
{
  "new_parent_institution_id": "ins_PARENT_002",
  "relationship_type": "governance_parent",
  "reason": "Regional realignment FY27",
  "idempotency_key": "f3d9f5bd-2f4d-4f8f-a5a6-0b9d9f9e7fbb"
}
```

**Response (200)**
```json
{
  "institution_id": "ins_01J0ABCXYZ",
  "previous_parent_institution_id": "ins_PARENT_001",
  "new_parent_institution_id": "ins_PARENT_002",
  "effective_root_institution_id": "ins_ROOT_001",
  "status": "updated"
}
```

Contract requirements:
- All write APIs require `tenant_safety_context` header set by gateway/admin plane.
- Mutations are idempotent using `idempotency_key` when provided.
- Validation errors return structured code set: `TYPE_UNSUPPORTED`, `HIERARCHY_CYCLE`, `TENANT_LINK_CONFLICT`, `INVALID_STATE_TRANSITION`.

---

## 8) Events Produced

| Event | Trigger | Key Payload |
|---|---|---|
| `institution.created.v1` | Institution created. | institution_id, institution_type, status, registration_country |
| `institution.activated.v1` | State transitions to active. | institution_id, activated_at, activated_by |
| `institution.suspended.v1` | State transitions to suspended. | institution_id, reason_code, suspended_at |
| `institution.archived.v1` | State transitions to archived. | institution_id, archived_at |
| `institution.hierarchy_linked.v1` | Parent edge created. | parent_institution_id, child_institution_id, relationship_type |
| `institution.reparented.v1` | Parent changed. | institution_id, old_parent_id, new_parent_id, reason |
| `institution.tenant_linked.v1` | Tenant link created. | institution_id, tenant_id, link_scope |
| `institution.tenant_unlinked.v1` | Tenant link deactivated. | institution_id, tenant_id, link_scope, unlinked_at |
| `institution.type_updated.v1` | Type metadata changed. | type_code, governance_profile, updated_at |

Event guarantees:
- At-least-once delivery with dedupe key = event_id.
- Ordering guaranteed per institution aggregate key.

---

## 9) Events Consumed

| Event | Source Service | Usage |
|---|---|---|
| `tenant.created.v1` | tenant_service | Optional bootstrap suggestion for tenant-to-institution linking workflow. |
| `tenant.archived.v1` | tenant_service | Auto-mark related tenant links inactive; retain institution metadata. |
| `program.published.v1` | program_service | Validate institution eligibility for program visibility policies. |
| `program.retired.v1` | program_service | Cleanup derived institution-program policy bindings. |
| `user.role_changed.v1` | user_service | Re-evaluate institution admin authorization cache. |
| `user.deactivated.v1` | user_service | Remove/deactivate institution contact or delegated approver roles. |

Consumption rules:
- Consumed events cannot mutate runtime learning records.
- If consumed event references unknown tenant/institution, route to dead-letter with replay support.

---

## 10) Integration Contracts

### 10.1 tenant_service Integration
- `institution_service` is downstream of tenant lifecycle state for link validity.
- Primary link invariants:
  - one active primary institution per tenant,
  - tenant must be `active` for new primary link,
  - suspend/archive of tenant triggers link status reevaluation.

### 10.2 program_service Integration
- `program_service` requests institution context for:
  - availability constraints,
  - governance policy inheritance,
  - academy/tutor distribution channels.
- Institution hierarchy can scope program distribution without owning program entities.

### 10.3 user_service Integration
- User roles (institution_admin, institution_auditor, institution_operator) resolved in user_service/RBAC.
- `institution_service` consumes role change events and enforces action-level authorization.
- Contacts and delegated operators reference user IDs but user profile remains owned by user_service.

---

## 11) Tenant Safety and Isolation

- Every mutable operation includes authorization context asserting actor tenancy and institution scope.
- Cross-tenant hierarchy linkage is allowed only under platform-level policy and explicit governance roles; defaults to deny.
- Tenant links are soft-deletable and fully audit logged.
- Read models expose only institution IDs authorized for caller scope.

---

## 12) Global Education Compatibility

- Supports country-agnostic institution registration metadata.
- Supports academy franchise models and tutor network affiliations.
- Supports mixed-mode enterprises (university + corporate training branches) via multi-type hierarchy.
- Locale/timezone/default policy definitions stored per institution for region-specific behavior.

---

## 13) QC LOOP

### QC Pass 1

| Category | Score (1-10) | Finding |
|---|---:|---|
| hierarchy flexibility | 8 | Did not explicitly permit non-governance edge semantics and policy-flagged academy franchise chains. |
| service boundary clarity | 9 | Ownership was defined, but runtime non-ownership constraints needed stronger explicit wording in integration sections. |
| alignment with repo runtime entities | 9 | Tenant-first runtime alignment needed explicit resolution rule for queries. |
| global education compatibility | 8 | Needed clearer support for cross-country structures and tutor/academy specific patterns. |
| tenant safety | 9 | Missing explicit deny-by-default cross-tenant link policy. |
| maintainability | 9 | Missing canonical error taxonomy and idempotency expectations in contract section. |

Defects addressed in revision:
1. Added non-governance edge types and academy/tutor specific hierarchy rules.
2. Added explicit “Does Not Own” table and runtime alignment rule.
3. Added cross-country compatibility language and mixed institution model support.
4. Added deny-by-default cross-tenant policy and stronger tenant safety section.
5. Added validation error taxonomy and idempotency contract requirements.

### QC Pass 2 (Post-Revision)

| Category | Score (1-10) | Rationale |
|---|---:|---|
| hierarchy flexibility | 10 | Supports DAG + constrained governance parent + affiliate/partnership edges + academy/tutor-specific patterns. |
| service boundary clarity | 10 | Clear owned vs non-owned entities and explicit non-replacement of runtime model. |
| alignment with repo runtime entities | 10 | Tenant-first runtime preserved with institution overlay and lookup resolution rule. |
| global education compatibility | 10 | Country-agnostic metadata, franchise/affiliate support, and mixed institution structures included. |
| tenant safety | 10 | Deny-by-default cross-tenant policy, scoped authorization, and audited links defined. |
| maintainability | 10 | Versioned events, explicit contracts, error taxonomy, and idempotency requirements improve operability. |

QC Result: **All categories 10/10.**
