# Notification Service Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5.7 | **Service:** `services/notification-service/`

---

## Capability Domain: §5.7 Communication Capabilities

Covers: messaging | notifications | workflow triggers | scheduling

---

## Service Boundary

The notification service is the platform's communication dispatch layer. It receives communication intents from domain services and routes them to the correct adapter (email, SMS, WhatsApp, push). It does NOT own communication channel logic — adapters do.

---

## Capabilities Defined

### CAP-NOTIFICATION-DISPATCH
- Receives notification intents and routes to the correct communication adapter
- Channel selection: driven by tenant config and user preference — not hardcoded
- Owner: `services/notification-service/action_routing.py`

### CAP-WORKFLOW-TRIGGERED-COMMS
- Notifications triggered by workflow engine events
- Examples: enrollment confirmation, assessment result, fee reminder, batch reminder
- Integrates with: `services/workflow-engine/`
- Owner: `services/notification-service/orchestration.py`

### CAP-SCHEDULED-COMMS
- Schedule notifications for future delivery (reminders, digests, announcements)
- Scheduling is config-driven — rules stored externally

---

## Service Files

- `services/notification-service/action_routing.py` — action-to-channel routing
- `services/notification-service/orchestration.py` — workflow-triggered comms
- `services/notification-service/test_orchestration.py`

---

## Adapters Used

- `integrations/communication/email_adapter.py`
- `integrations/communication/sms_adapter.py`
- `integrations/communication/whatsapp_adapter.py`

---

## Auth Exception

**Auth mechanism: HS256 shared-secret** (exception ref: B05-002). This service deviates from the platform-wide RS256 JWT standard established in FA-004a.

The notification service processes internal dispatch commands from trusted domain services over the internal network. It does not validate end-user RS256 tokens directly on its dispatch path. HS256 was used to decouple the dispatch layer from a dependency on the auth-service JWKS endpoint.

**Impact:** External-facing notification routes (e.g., learner inbox retrieval) must pass through an RS256-validating gateway or token-exchange layer before reaching this service. Tracked for remediation to RS256 in line with FA-004a.

---

## References

- Master Spec §5.7
- `docs/contracts/communication-adapter-contract.md`
- `docs/qc/communication-workflow-validation-report.md` — PASS 10/10
