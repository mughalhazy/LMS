# Standards Support

**Location:** `Repo/docs/integrations/standards-support.md` | **Type:** Integration Spec | **Last reviewed:** 2026-05-26

Defines the e-learning standards supported by the LMS, their supported feature sets, and key implementation constraints.

---

## SCORM 1.2

**Supported features:**
- Launch and tracking via LMS API (`LMSInitialize`, `LMSSetValue`, `LMSCommit`, `LMSFinish`)
- Completion status, score reporting, lesson location, suspend/resume data
- Basic sequencing through SCO-level navigation within a package

**Implementation notes:** Use a SCORM runtime wrapper for browser communication, enforce 4 KB suspend_data limits, and normalize completion data into internal progress records.

---

## SCORM 2004

**Supported features:**
- Full SCORM Runtime API support (`Initialize`, `GetValue`, `SetValue`, `Commit`, `Terminate`)
- Sequencing and Navigation (Simple Sequencing rules)
- Richer data model including interactions, objectives, and success/completion separation

**Implementation notes:** Support 2nd/3rd/4th edition manifests, validate sequencing rules at import time, and map `cmi.success_status` + `cmi.completion_status` to LMS completion policies.

---

## xAPI

**Supported features:**
- Statement ingestion (`actor`, `verb`, `object`, `result`, `context`)
- LRS integration for storing and querying learning records
- Support for learning events outside LMS (mobile apps, simulations, offline sync)

**Implementation notes:** Provide an xAPI endpoint and/or connector to external LRS, secure with OAuth2, and implement verb/profile governance to avoid inconsistent reporting semantics.

---

## LTI 1.3

**Supported features:**
- OIDC login initiation and LTI message launch (Resource Link Request)
- Deep Linking (Content-Item selection)
- Names and Role Provisioning Services (NRPS) and Assignments and Grades Service (AGS)

**Implementation notes:** Implement JWT validation with platform JWKS rotation, enforce nonce/state checks, and maintain per-platform registrations (issuer, client_id, deployment_id, keyset URL).


---

## See also
- `docs/integrations/hris-sync-spec.md` � HRIS sync spec
- `docs/integrations/lti-consumer-spec.md` � LTI consumer spec
- `docs/integrations/lti-provider-spec.md` � LTI provider spec
- `docs/integrations/webhook-system-spec.md` � webhook system spec
