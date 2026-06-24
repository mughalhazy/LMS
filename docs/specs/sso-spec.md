# SSO Provider Specification

**Type:** Service Specification | **Last reviewed:** 2026-05-30

Authentication flow and required configuration fields per SSO provider. See `docs/architecture/security-architecture.md` for the security architecture reference.

---

## Service Architecture — Two-Layer SSO Boundary

SSO is implemented across two services with distinct responsibilities. A caller never interacts with `sso-service` directly; all external-facing SSO traffic enters through `auth-service`.

### Layer 1 — auth-service (consumer-facing entry point)

`auth-service` is the platform identity gateway. It owns session creation and exposes the SSO surface that clients and the API gateway interact with directly.

SSO routes in auth-service:

| Route | Method | Purpose |
|---|---|---|
| `/api/v1/auth/tenant?domain={domain}` | GET | Tenant discovery by email domain — resolves which tenant a user belongs to before login. Used to determine SSO provider for pre-login flow. |
| `/api/v1/auth/sso/initiate` | POST | SSO initiation — accepts `tenant_id`, `provider_type`, `redirect_uri`, optional `correlation_id`. Delegates provider-specific flow setup to sso-service, returns redirect or auth URL. |
| `/api/v1/auth/sso/callback` | POST | SSO callback — accepts `tenant_id`, `provider_type`, `code_or_assertion`, `correlation_id`. Delegates assertion/code validation to sso-service, then creates an authenticated platform session and issues JWT. |

auth-service owns:
- Platform session lifecycle (JWT issuance, session validation).
- Provider-type routing logic (which sso-service flow to invoke).
- Correlation of SSO result to platform identity.
- Session creation after a successful SSO assertion exchange.

auth-service does NOT own:
- Provider-specific protocol flow (SAML assertion parsing, OIDC token exchange, OAuth2 code exchange).
- Provider configuration storage (config fields live in sso-service).
- Token validation against provider JWKs or certificate verification.

### Layer 2 — sso-service (flow orchestration)

`sso-service` is the SSO protocol execution layer. It runs behind the identity boundary and is not exposed directly to clients or the API gateway.

Routes in sso-service:

| Route | Method | Purpose |
|---|---|---|
| `/api/v1/sso/providers` | GET | Returns the provider matrix — supported provider types and their configuration requirements per tenant. |
| `/api/v1/sso/initiate` | POST | Executes provider-specific pre-auth flow (SAML redirect construction, OIDC authorization URL, OAuth2 redirect). Called by auth-service, not clients. |
| `/api/v1/sso/callback` | POST | Executes provider-specific callback handling (SAML assertion validation, OIDC token exchange and ID token verification, OAuth2 code exchange). Returns normalized identity claims to auth-service. |

sso-service owns:
- All provider-specific protocol logic (SAML, OAuth2, OIDC).
- Provider configuration management (required fields per provider — see table below).
- Signature/certificate validation, token introspection, claim normalization.
- Provider matrix registry (which providers are supported and how they are configured).

sso-service does NOT own:
- Platform session creation or JWT issuance (auth-service responsibility).
- User identity storage or credential management (auth-service/user-service responsibility).
- Consumer-facing API surface (auth-service is the gateway).

### Delegation Pattern

```
Client / API Gateway
    │  POST /api/v1/auth/sso/initiate
    ▼
auth-service
    │  resolve provider type, delegate flow setup
    │  POST /api/v1/sso/initiate  (internal)
    ▼
sso-service
    │  build provider-specific redirect / auth URL
    ▼
auth-service → returns redirect to client

--- (provider interaction happens externally) ---

Client / API Gateway
    │  POST /api/v1/auth/sso/callback
    ▼
auth-service
    │  delegate assertion / code validation
    │  POST /api/v1/sso/callback  (internal)
    ▼
sso-service
    │  validate assertion/token, normalize claims
    ▼
auth-service
    │  map claims to platform identity, create session, issue JWT
    ▼
Client ← session token
```

### References

- `Repo/backend/services/auth-service/app/main.py` — auth-service SSO routes (§8 of auth-service-spec.md)
- `Repo/backend/services/sso-service/app/main.py` — sso-service flow orchestration routes
- `docs/architecture/security-architecture.md` — full security architecture reference
- `docs/specs/auth-service-spec.md` — auth-service spec §8 for SSO route contract

---

## Provider Configuration

Required configuration fields per SSO provider type. These fields are owned and validated by `sso-service`.

| sso_provider | authentication_flow | required_fields |
| --- | --- | --- |
| SAML 2.0 | Browser redirects user to Identity Provider (IdP) using SP-initiated or IdP-initiated SAML flow; IdP returns signed SAML assertion to Assertion Consumer Service (ACS); service validates signature, audience, and conditions, then creates authenticated session. | idp_entity_id, idp_sso_url, idp_x509_certificate, sp_entity_id, acs_url, nameid_format, attribute_mapping (email, first_name, last_name, role), assertion_signature_required, response_signature_required |
| OAuth 2.0 | Authorization Code flow: user is redirected to authorization server; after consent/login, authorization code is returned to redirect URI; backend exchanges code for access token (and optional refresh token), validates token/introspection, then maps identity and creates session. | client_id, client_secret, authorization_endpoint, token_endpoint, redirect_uri, scopes (openid/profile/email or provider-specific), userinfo_endpoint_or_introspection_endpoint, state_validation_enabled, pkce_required |
| OpenID Connect (OIDC) | Authorization Code + PKCE: user authenticates at OIDC provider; code is exchanged for ID token and access token; service validates ID token signature, issuer, audience, nonce, expiration, then establishes authenticated session with mapped claims. | issuer, client_id, client_secret (or private_key_jwt settings), authorization_endpoint, token_endpoint, jwks_uri, redirect_uri, scopes (openid profile email), nonce_validation_enabled, claim_mapping (sub, email, name, groups/roles) |
