# B2P07 — Audit and Policy Layer Design

## Purpose
Design an **independent** audit logging and policy enforcement layer that:
- tracks capability usage,
- tracks config changes,
- tracks entitlement changes,
- enforces policy decisions consistently,
- preserves immutable, tamper-evident compliance evidence.

This layer is intentionally separated from usage metering and entitlement business logic ownership.

---

## Scope & Non-Goals (QC Alignment)

### In scope
- Canonical audit event capture for security/compliance-critical actions.
- Real-time policy decision point (PDP) with explicit allow/deny/obligations outcomes.
- Tamper-evident immutable audit ledger and evidence export pipeline.
- Correlated tracing across request lifecycle (`request_id`, `correlation_id`, `actor`, `tenant`).
- Compliance-ready retention, legal hold, and chain-of-custody controls.

### Out of scope
- Usage billing/metering aggregation (volume/rate/cost analytics).
- Entitlement resolution logic (plan/segment/country/add-on rights computation).
- Config value resolution/merge behavior.
- Domain service business workflows and UI presentation logic.

### Explicit QC guarantees
- **No overlap with usage metering:** audit records capture control-plane and security evidence, not billable counters.
- **No duplication of entitlement logic:** policy layer consumes entitlement decisions as read-only inputs; it never computes rights.
- **Independent service boundary:** dedicated interfaces, storage, and lifecycle; no dependence on metering pipelines.
- **Compliance support:** immutable storage, signed records, retention controls, and evidence export.
- **Clear logging boundaries:** canonical event classes with ownership matrix and strict event taxonomy.

---

## Service Design (Modules + Responsibilities)

## 1) `PolicyEnforcementAPI` (PEP-facing entrypoint)
**Responsibility:** Runtime interface for services/gateways that need policy decisions.

- `evaluate(requestContext, action, resource, attributes)`
- `evaluateBatch(decisionRequests[])`
- Returns structured decision envelope:
  - `decision`: `ALLOW | DENY | CHALLENGE | REQUIRE_JIT_APPROVAL`
  - `policy_id`, `policy_version`, `reason_codes[]`
  - `obligations[]` (e.g., redact fields, require MFA)
  - `decision_id`, `evaluated_at`

## 2) `PolicyDecisionEngine` (deterministic PDP)
**Responsibility:** Evaluate policy rules in fixed order and produce deterministic outcomes.

- Fixed precedence:
  1. global deny/safety rules,
  2. tenant security baseline,
  3. resource/action rules,
  4. contextual constraints (time/IP/risk/session assurance),
  5. break-glass/JIT exceptions.
- Decision determinism based on pinned policy snapshot versions.
- Emits policy trace for explainability/compliance.

## 3) `PolicyRegistryPort` (read-only rule source)
**Responsibility:** Retrieve signed, versioned policy bundles.

- Loads policy snapshot by `policy_bundle_id` + `version`.
- Validates signature before activation.
- Uses atomic snapshot swap for runtime updates.

## 4) `ExternalGuardPorts` (read-only boundary integrations)
**Responsibility:** Ingest required context without duplicating upstream ownership.

- `EntitlementDecisionPort`: reads already-computed entitlement status (`allowed/denied`) only.
- `ConfigContextPort`: reads resolved config selectors only (no merge logic).
- `IdentityAssurancePort`: reads auth strength/MFA/session risk posture.
- All ports are read-only and cacheable with bounded TTL.

## 5) `AuditCaptureSDK` (producer contract)
**Responsibility:** Standardized event capture from all producing services.

- Enforces required envelope:
  - `event_id`, `event_type`, `occurred_at`, `tenant_id`, `actor_id?`,
  - `target_ref`, `action`, `outcome`, `decision_id?`,
  - `request_id`, `correlation_id`, `source_service`, `schema_version`.
- Rejects malformed events and emits producer error diagnostics.
- Supports synchronous (critical) and asynchronous (non-blocking) publish modes.

## 6) `AuditIngestionGateway`
**Responsibility:** Validate, normalize, and route audit events to immutable storage.

- Performs schema validation + PII minimization + field-level classification.
- Adds server-side integrity metadata (`ingested_at`, `ingest_node_id`, `payload_hash`).
- Writes to append-only log topic and immutable ledger writer.

## 7) `ImmutableAuditLedger`
**Responsibility:** Store tamper-evident append-only audit records.

- WORM-compatible storage policy.
- Hash-chained records (`prev_hash`, `record_hash`) per partition stream.
- Periodic Merkle root anchoring + external notarization hook.
- No update/delete APIs; only append + legal-hold markers.

## 8) `ComplianceEvidenceService`
**Responsibility:** Query/export auditable evidence with chain-of-custody.

- Supports scoped retrieval by tenant, actor, policy, control, time window.
- Produces signed export manifests (hashes + record counts + watermark IDs).
- Enforces RBAC for auditors/compliance officers and logs all export access.

## 9) `RetentionAndLegalHoldManager`
**Responsibility:** Compliance lifecycle controls over immutable records.

- Retention classes (e.g., 1y/3y/7y/custom by regulation domain).
- Legal hold supersedes expiry.
- Evidence of purge execution stored as immutable control events.

## 10) `AuditTaxonomyManager`
**Responsibility:** Maintain strict logging boundaries and event semantics.

- Owns canonical event families and required fields.
- Prevents semantic drift and duplicate event meaning across teams.
- Versioned taxonomy changes with migration guidance.

---

## Canonical Logging Boundaries (No Metering Overlap)

### A) Audit & policy layer **owns**
1. **Capability usage control events** (security/compliance context):
   - `capability.access.requested`
   - `capability.access.decisioned`
   - `capability.access.denied`
   - `capability.break_glass.invoked`

2. **Config change control events**:
   - `config.change.requested`
   - `config.change.approved`
   - `config.change.applied`
   - `config.change.reverted`

3. **Entitlement change governance events**:
   - `entitlement.change.proposed`
   - `entitlement.change.approved`
   - `entitlement.change.applied`
   - `entitlement.change.revoked`

4. **Policy lifecycle and enforcement events**:
   - `policy.bundle.published`
   - `policy.decision.evaluated`
   - `policy.override.granted`
   - `policy.override.expired`

### B) Usage metering layer **owns** (explicitly separate)
- `usage.units.recorded`, `usage.aggregated`, `usage.invoice.projected`, etc.
- Cardinality/rate/cost/consumption analytics for billing.

### C) Boundary rule
- Same business action may emit **both**:
  - one audit/policy evidence event (this layer), and
  - one metering event (metering layer),
  with different schemas, topics, storage, retention classes, and consumers.

---

## Policy Enforcement Model (Independent, No Entitlement Duplication)

`final_authorization = entitlement_input AND policy_decision`

- Entitlement input is provided by authoritative entitlement service.
- Policy layer can only **further constrain** or require obligations/challenges.
- Policy layer cannot grant capability beyond entitlement allow.
- This preserves separation of rights computation vs runtime governance.

---

## Audit Flow (End-to-End)

## Flow 1: Capability usage with policy check
1. Caller invokes protected action at gateway/service boundary.
2. PEP calls `PolicyEnforcementAPI.evaluate(...)` with context and action.
3. PDP evaluates rule snapshot + external read-only context ports.
4. PDP returns decision (`ALLOW/DENY/...`) + policy trace metadata.
5. Service executes/blocks action according to decision.
6. `AuditCaptureSDK` emits:
   - request event,
   - decision event,
   - outcome event.
7. `AuditIngestionGateway` validates and enriches events.
8. `ImmutableAuditLedger` appends hash-chained records.
9. Observability emits metrics/alerts for anomalous denies or override spikes.

## Flow 2: Config change governance
1. Admin submits config change request with change ticket reference.
2. Policy layer evaluates actor authority + change window + approval requirements.
3. On approval, config service applies change (still owning config semantics).
4. Audit layer records request/approval/apply events with before/after value hashes.
5. Ledger stores immutable evidence for compliance review.

## Flow 3: Entitlement change governance
1. Entitlement admin proposes change in entitlement service workflow.
2. Policy layer validates SoD, dual-control, and approval policy.
3. Entitlement service applies canonical rights update (ownership retained there).
4. Audit layer records proposal/approval/application/revocation lifecycle events.
5. Compliance evidence exports can reconstruct full decision chain.

---

## Security & Immutability Controls

- mTLS + workload identity for service-to-service trust.
- Envelope signing at ingestion boundary (producer identity + payload hash).
- Append-only storage with hash chain and periodic integrity verification jobs.
- WORM + object lock for regulated retention classes.
- Encryption at rest (KMS-managed keys) and in transit.
- Strict least-privilege access with JIT privileged sessions.
- Read/export access itself is audited immutably.

---

## Compliance Readiness Controls

- SOC2/ISO-style evidence traceability via immutable decision and change records.
- Retention policy by control family/jurisdiction.
- Legal hold and defensible deletion workflow.
- Signed, reproducible evidence exports with manifest + checksum verification.
- Control mapping fields (`control_id`, `policy_id`, `evidence_ref`) in event schema.

---

## Data Contracts (Minimal Canonical Schemas)

## `policy.decision.evaluated`
- `decision_id`, `tenant_id`, `actor_id`, `action`, `resource_ref`,
- `entitlement_input` (`allow|deny|unknown`),
- `policy_decision` (`allow|deny|challenge|jit_required`),
- `policy_id`, `policy_version`, `reason_codes[]`, `obligations[]`,
- `request_id`, `correlation_id`, `occurred_at`.

## `config.change.applied`
- `change_id`, `tenant_id`, `actor_id`, `config_scope`, `config_key`,
- `previous_value_hash`, `new_value_hash`,
- `approval_ref`, `ticket_ref`, `policy_decision_id`,
- `request_id`, `occurred_at`.

## `entitlement.change.applied`
- `change_id`, `tenant_id`, `actor_id`, `subject_ref`,
- `entitlement_before_hash`, `entitlement_after_hash`,
- `approval_ref`, `policy_decision_id`, `reason_codes[]`,
- `request_id`, `occurred_at`.

---

## Failure Modes & Safe Defaults

- **Policy engine unavailable:** fail closed for protected actions; emit `policy.decision.unavailable`.
- **Audit ingestion unavailable:** block high-risk control-plane mutations (config/entitlement changes) until durable audit path is restored.
- **Ledger integrity mismatch:** raise sev1 incident; freeze export until re-verification.
- **External context timeout (entitlement/config/auth assurance):** apply conservative deny or challenge based on action criticality policy.

---

## QC FIX RE QC 10/10 Mapping

- **No overlap with usage metering:** explicit event taxonomy split and ownership boundary.
- **No duplication of entitlement logic:** entitlement consumed read-only; no rights computation in policy/audit layer.
- **Must be independent:** dedicated API, PDP, ingestion, ledger, evidence export, and lifecycle managers.
- **Must support compliance needs:** immutable ledger, retention/legal hold, signed exports, chain-of-custody, control mappings.
- **Clear logging boundaries:** canonical audit event classes and taxonomy governance with anti-duplication policy.
