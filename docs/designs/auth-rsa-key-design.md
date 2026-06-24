> NOTE: docs/06_decisions/ADR-001_PROJECT_FOUNDATION.md Decision 5 is the policy authority for authentication token standards (RS256 mandatory; HS256 exceptions list).
> This document provides implementation design detail. When conflicts arise, ADR-001 Decision 5 governs.
> Last reviewed: 2026-06-22

# Auth Service — RSA Key Design (FA-004a)

**Location:** `Repo/docs/designs/auth-rsa-key-design.md`
**Status:** ACTIVE — governing doc for FA-004a implementation
**Last updated:** 2026-05-31
**Spec anchor:** `Repo/docs/specs/auth-service-spec.md` §5 (token signing), §4.8 (JWKS)

---

## 1) Problem

`auth-service` currently uses HS256 (HMAC-SHA256 with a shared secret) for JWT signing. The governing spec (auth-service-spec.md §5) requires **RS256 or ES256** (asymmetric signing). With HS256, any service that can verify tokens can also issue them — a security violation in a multi-service platform.

---

## 2) Algorithm Choice

**RS256** (RSA-PKCS1v15, SHA-256) — chosen over ES256 for:
- Wider library support across services that need to verify tokens
- Simpler JWKS representation (single `n`, `e` fields)
- `cryptography` library available in Python 3.12 environment (installed 2026-05-31)

Key size: **RSA-2048** (adequate for platform scale; upgrade to 4096 when key rotation infrastructure exists)

---

## 3) Key Generation

Keys are generated using the `cryptography` library at service startup if env vars are absent.

### Production / Staging
Generate a key pair and export as PEM:

```bash
python -c "
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

priv = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()).decode()
pub = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()

print('JWT_PRIVATE_KEY:', repr(priv))
print('JWT_PUBLIC_KEY:', repr(pub))
"
```

Store the output in environment variables (with literal `\n` preserved).

### Development (auto-generate)
If `JWT_PRIVATE_KEY` env var is absent, the service generates a fresh ephemeral key pair at startup. This means tokens are invalidated on restart — acceptable for development.

---

## 4) Environment Variables

| Variable | Required | Description |
|---|---|---|
| `JWT_PRIVATE_KEY` | Recommended | PEM-encoded RSA private key (for signing) |
| `JWT_PUBLIC_KEY` | Optional | PEM-encoded RSA public key (derived from private key if absent) |
| `JWT_SHARED_SECRET` | Legacy | Still read for backward-compat; ignored when `JWT_PRIVATE_KEY` present |

---

## 5) Key ID (kid)

`kid` = first 16 hex chars of SHA-256 digest of the DER-encoded public key.

Used in:
- JWT header: `{"alg": "RS256", "typ": "JWT", "kid": "<kid>"}`
- JWKS response: `{"keys": [{"kty": "RSA", "kid": "<kid>", "alg": "RS256", "use": "sig", "n": "...", "e": "AQAB"}]}`

---

## 6) JWKS Endpoint

`GET /.well-known/jwks.json` returns:

```json
{
  "keys": [
    {
      "kty": "RSA",
      "kid": "<16-char hex>",
      "alg": "RS256",
      "use": "sig",
      "n": "<base64url-encoded modulus>",
      "e": "AQAB"
    }
  ]
}
```

Other services (e.g. rbac-service, API gateway) can fetch this endpoint to obtain the public key for token verification without needing a shared secret.

---

## 7) Migration Path

1. Deploy with new RS256 signing — all new tokens use RS256
2. Existing HS256 tokens expire naturally within 15 minutes (access TTL) / 7 days (refresh TTL)
3. Services that call `validate_token()` directly must update to RS256 verification — or use JWKS discovery
4. `JWT_SHARED_SECRET` env var retained for local development fallback only

---

## 8) Token Claims (unchanged from spec §5)

```json
{
  "alg": "RS256",
  "typ": "JWT",
  "kid": "<kid>"
}
{
  "sub": "<user_id>",
  "tenant_id": "<tenant_id>",
  "session_id": "<session_id>",
  "roles": ["<role>"],
  "scope": "lms.api",
  "iat": <unix_ts>,
  "exp": <unix_ts>
}
```
