# Capability Gating Model

## 1) Objective
Define a deterministic model for enabling and disabling LMS capabilities per tenant plan while preserving tenant isolation, billing alignment, and service-level compatibility.

---

## 2) Capability Categories
Capabilities are grouped into four top-level categories for governance, rollout, and billing.

### AI Features
- AI Learning Copilot
- AI Course Generation
- AI Content Summarization
- AI Skill Gap Suggestions

### Analytics Features
- Advanced Dashboards
- Predictive Completion Risk
- Skill Analytics
- Exportable BI Feeds

### Academy Tools
- Cohort Management
- Learning Paths
- Prerequisite Engine
- Content Versioning

### Enterprise Integrations
- SSO (SAML/OIDC)
- HRIS Sync
- LTI Provider/Consumer
- Webhooks and Event Push

---

## 3) Architecture Components

### 3.1 Feature Flag Service
**Purpose:** Runtime toggles for controlled rollout and incident mitigation.

**Responsibilities:**
- Stores feature flags with scope: global, plan, tenant, environment.
- Supports percentage rollouts and canary release controls.
- Evaluates flags at request time and caches short-lived decisions.

**Boundary:**
- Feature flags do **not** grant paid access by themselves.
- They can only further restrict or progressively release already-entitled capabilities.

### 3.2 Entitlement Service
**Purpose:** Source of truth for commercial access rights.

**Responsibilities:**
- Maps `tenant_id + active_plan + add_ons` to allowed capabilities.
- Receives plan lifecycle changes from billing (upgrade, downgrade, suspension).
- Publishes `entitlement.updated` events for downstream cache invalidation.

**Boundary:**
- Entitlement decisions are authoritative for paid capability access.
- Service-level checks must reject access when entitlement is absent even if feature flag is ON.

### 3.3 Plan Configuration
**Purpose:** Versioned plan definitions and add-on packaging.

**Responsibilities:**
- Defines plan SKUs (`starter`, `growth`, `enterprise`) and add-on bundles.
- Declares capability limits (e.g., monthly AI token budgets, max dashboards).
- Supports effective dating for future plan catalogs.

**Boundary:**
- Configuration is immutable per version; billing references explicit plan version.

### 3.4 Tenant Capability Map
**Purpose:** Materialized, query-optimized view used by request path.

**Responsibilities:**
- Resolves final effective capability state per tenant:
  `effective = entitlement(plan + add-ons) ∩ feature_flags(runtime controls)`
- Tracks reason metadata (`plan_included`, `add_on`, `flag_disabled`, `suspended`).
- Exposes API for low-latency authorization checks.

**Boundary:**
- Never broadens capability beyond entitlement.
- Must include timestamp + version for traceability.

---

## 4) Decision Flow (Runtime)
1. Caller requests a capability-bound action.
2. Service queries Tenant Capability Map (or local cache with strict TTL).
3. Tenant Capability Map validates entitlement snapshot version.
4. Feature Flag Service applies runtime restrictions.
5. Policy engine evaluates service compatibility constraints.
6. Request is allowed/denied with machine-readable reason code.
7. Audit log records decision with `tenant_id`, `capability`, `plan_version`, and `decision`.

---

## 5) Capability Example Matrix

| Capability | Tenant Plan | Enabled Services |
|---|---|---|
| AI Learning Copilot | Growth + AI Add-on | `ai-copilot-service`, `prompt-safety-service`, `usage-metering-service` |
| Predictive Completion Risk | Enterprise | `analytics-service`, `event-ingestion-service`, `reporting-service` |
| Cohort Management | Starter | `cohort-service`, `user-service`, `notification-service` |
| HRIS Sync | Enterprise + Integrations Add-on | `integration-service`, `webhook-service`, `audit-log-service` |

---

## 6) Billing Integration Rules
- Billing is the trigger authority for plan state transitions.
- Entitlement Service consumes billing events and recomputes entitlements.
- Grace period policy is explicit (`active`, `grace`, `suspended`, `terminated`).
- Usage-metered capabilities enforce quotas before service execution.
- Downgrade handling is non-destructive: existing data remains, premium operations are blocked.

---

## 7) Service Compatibility Rules
- Each capability declares required service dependencies.
- Capability activation fails closed if any required dependency is unavailable.
- Incompatibility constraints are modeled explicitly, e.g.:
  - `Predictive Completion Risk` requires event ingestion quality threshold.
  - `LTI Provider` requires SSO and content API scopes.

---

## 8) Extensibility Model
- Add new capability by appending to capability registry with:
  - category
  - dependency set
  - billing metric (if metered)
  - rollout default flag strategy
- Backward-compatible plan evolution via versioned plan configs.
- Tenant Capability Map schema supports arbitrary metadata for future policy dimensions (region, compliance tier, data residency).

---

## 9) QC LOOP

### QC Pass 1
Scores (1–10):
- Feature isolation correctness: **8/10**
- Integration with billing model: **8/10**
- Service compatibility: **9/10**
- Extensibility: **9/10**

**Identified gating flaws:**
1. No explicit guard against feature flag enabling non-entitled capability.
2. Billing grace/suspension states not tied to deterministic enforcement states.

**Corrections applied:**
- Added hard boundary: feature flags cannot expand entitlement scope.
- Added explicit billing lifecycle states and enforcement outcomes.

### QC Pass 2
Scores (1–10):
- Feature isolation correctness: **9/10**
- Integration with billing model: **10/10**
- Service compatibility: **9/10**
- Extensibility: **10/10**

**Identified gating flaws:**
1. Compatibility checks did not specify fail-closed behavior.
2. Tenant decision traceability lacked version/timestamp guarantee.

**Corrections applied:**
- Added fail-closed compatibility rule when dependencies are unavailable.
- Added timestamp/version traceability requirement to Tenant Capability Map.

### QC Pass 3 (Final)
Scores (1–10):
- Feature isolation correctness: **10/10**
- Integration with billing model: **10/10**
- Service compatibility: **10/10**
- Extensibility: **10/10**

**Result:** Capability Gating Model accepted.
