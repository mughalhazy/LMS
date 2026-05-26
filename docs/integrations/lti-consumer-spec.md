# LTI Consumer Specification

**Location:** `Repo/docs/integrations/lti-consumer-spec.md` | **Type:** Integration Spec | **Last reviewed:** 2026-05-26

Describes the three operational phases for the LMS acting as an LTI 1.3 Consumer (platform), integrating external tools.

---

## External Tool Integration

### Configuration Steps

- Register LMS as an LTI 1.3 platform (consumer) with each tool using `issuer`, `client_id`, `deployment_id`, launch URL, and JWKS endpoint.
- Store tool metadata: OIDC auth initiation URL, target link URI, public key set URL, AGS/NRPS service endpoints, and allowed message types.
- Configure trust and security controls: redirect URI allowlist, nonce/state TTL, key rotation schedule, and tenant/environment mapping.

**Result:** LMS can securely discover and trust external tools, route launches to the right tool configuration, and enforce tenant-scoped integration governance.

---

## Launch Process

### Steps

- User clicks external activity in LMS; LMS creates OIDC auth request (`login_hint`, `lti_message_hint`, `state`, `nonce`) and redirects to tool initiation/login endpoint.
- Tool returns to LMS launch endpoint with `id_token` (JWT); LMS validates signature (JWKS), issuer/audience, deployment_id, nonce, exp/iat, and message type.
- LMS builds launch context (user role, course/resource link, locale, custom params) and completes LTI Resource Link launch session.

**Result:** Learner/instructor is launched into the tool with authenticated context, correct role/course binding, and replay-resistant security checks.

---

## Result Capture

### Grade Passback (AGS)

- LMS enables AGS for line item discovery/creation and score publishing; tool posts score payloads tied to user and resource.
- LMS validates incoming score requests (service token scopes, tool identity, line item ownership) and normalizes scores/status into gradebook schema.
- LMS writes grade/progress events for downstream analytics, transcripts, and completion workflows; retries/idempotency guard duplicates.

**Result:** Tool outcomes are reflected in LMS gradebook and progress tracking with auditable, consistent, and near-real-time result synchronization.


---

## See also
- `docs/integrations/lti-provider-spec.md` � LTI provider spec
- `docs/integrations/standards-support.md` � integration standards reference
- `docs/api/integration-api.md` � integration API
