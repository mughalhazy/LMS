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
- `GET /health`
- `GET /providers`
- `POST /sso/initiate`
- `POST /sso/callback`

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

## Notes
This scaffold models required configuration fields from `/docs/specs/sso_spec.md`, and follows the identity boundary from core architecture docs by keeping SSO in a dedicated service that can sit behind the API gateway/identity layer.
