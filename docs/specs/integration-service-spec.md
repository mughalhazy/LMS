# Integration Service Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §4 | **Service:** `services/integration-service/`

---

## Scope

The integration service manages all external system integrations: HRIS/directory sync, webhooks, LTI, and third-party adapter routing. It is the platform's outbound and inbound integration hub.

---

## Capabilities Defined

### CAP-HRIS-SYNC
- Sync users, org hierarchy, enrollments, and completions from external HR systems
- Sync modes: scheduled batch, event-triggered delta, manual trigger
- Spec ref: `docs/integrations/hris-sync-spec.md`

### CAP-WEBHOOK-DELIVERY
- Deliver platform domain events to external subscriber endpoints
- Retry policy, DLQ, payload signing, delivery status tracking
- Spec ref: `docs/integrations/webhook-system-spec.md`

### CAP-LTI-INTEROPERABILITY
- LTI consumer: launch external tools from within the platform
- LTI provider: expose platform courses as launchable tools
- Spec refs: `docs/integrations/lti-consumer-spec.md`, `docs/integrations/lti-provider-spec.md`

### CAP-ADAPTER-ROUTING
- Route integration requests to the correct adapter implementation
- All adapters registered in platform integration layer (`B2P08`)
- Adapter registry: config-driven, hot-swappable without deployment

---

## API

- `docs/api/integration-api.md` — integration endpoints

---

## References

- Master Spec §4
- `docs/designs/platform-integration-layer-design.md`
- `docs/integrations/standards-support.md`
- `docs/specs/adapter-inventory.md`
