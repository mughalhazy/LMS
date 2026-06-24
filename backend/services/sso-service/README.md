# SSO Service

Generated single sign-on service for LMS identity boundary.

## Providers supported
- SAML 2.0
- OAuth 2.0
- OpenID Connect (OIDC)

## Auth flows
- **SAML**: SP-initiated / IdP-initiated assertion flow
- **OAuth2**: Authorization Code flow
- **OIDC**: Authorization Code + PKCE flow

## API

Scope: SSO provider orchestration — flow management, token exchange, provider config. Auth-service SSO routes (`/api/v1/auth/sso/...`) are the consumer-facing entry point; they delegate flow execution to this service.

- `GET /health`
- `GET /metrics`
- `GET /api/v1/sso/providers`
- `POST /api/v1/sso/initiate`
- `POST /api/v1/sso/callback`

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Notes
This scaffold models required configuration fields from `/docs/specs/sso-spec.md`, and follows the identity boundary from core architecture docs by keeping SSO in a dedicated service that can sit behind the API gateway/identity layer.
