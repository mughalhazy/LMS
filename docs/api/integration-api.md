# Integration API

**Type:** API Reference | **Last reviewed:** 2026-05-26

External integration endpoints covering HRIS, CRM, LTI, and webhook ingestion with their authentication requirements.

---

| integration_type | endpoint | authentication |
--- | --- | ---
HRIS | `POST /api/integrations/hris/employees/sync` | OAuth 2.0 Client Credentials + signed payload (HMAC-SHA256)
CRM | `POST /api/integrations/crm/contacts/upsert` | OAuth 2.0 Authorization Code + scoped access token
LTI tools | `POST /api/integrations/lti/launch` | LTI 1.3 (OIDC login + JWT signed with platform public key)
webhooks | `POST /api/integrations/webhooks/events` | Webhook secret signature (HMAC-SHA256) + optional IP allowlist


---

## See also
- `docs/integrations/hris-sync-spec.md` � HRIS sync spec
- `docs/integrations/lti-consumer-spec.md` � LTI consumer spec
- `docs/integrations/webhook-system-spec.md` � webhook system spec
