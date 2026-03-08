integration_type | endpoint | authentication
--- | --- | ---
HRIS | `POST /api/integrations/hris/employees/sync` | OAuth 2.0 Client Credentials + signed payload (HMAC-SHA256)
CRM | `POST /api/integrations/crm/contacts/upsert` | OAuth 2.0 Authorization Code + scoped access token
LTI tools | `POST /api/integrations/lti/launch` | LTI 1.3 (OIDC login + JWT signed with platform public key)
webhooks | `POST /api/integrations/webhooks/events` | Webhook secret signature (HMAC-SHA256) + optional IP allowlist
