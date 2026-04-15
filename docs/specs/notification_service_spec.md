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

## References

- Master Spec §5.7
- `docs/architecture/communication_adapter_interface_contract.md`
- `docs/qc/B7P06_communication_workflow_validation_report.md` — PASS 10/10
