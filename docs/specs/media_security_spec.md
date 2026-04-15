# Media Security Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5.11 | **Service:** `services/media-security/`

---

## Capability Domain: §5.11 Content Protection Capabilities

Covers: secure media delivery | watermarking | session control | anti-piracy enforcement

---

## Service Boundary

The media security service controls access to protected content. It enforces entitlement-gated playback, injects watermarks, manages session tokens, and enforces anti-piracy controls. It integrates with the media pipeline but does not store media content.

---

## Capabilities Defined

### CAP-SECURE-MEDIA-DELIVERY
- Tokenised playback URLs — content is never publicly accessible
- Token includes: tenant_id, user_id, content_id, expiry, IP binding (optional)
- Tokens are short-lived and non-transferable
- Interface: `docs/architecture/media_security_interface_contract.md`

### CAP-WATERMARKING
- Inject visible or forensic watermarks into video streams
- Watermark payload: user_id, session_id, timestamp
- Enables source identification for leaked content

### CAP-SESSION-CONTROL
- Enforce concurrent session limits per user
- Revoke active sessions on entitlement change or security trigger
- Session state stored in media security service

### CAP-ANTI-PIRACY-ENFORCEMENT
- Rate limiting on stream requests
- Anomaly detection for unusual access patterns (multiple IPs, excessive bandwidth)
- Automatic session revocation on policy breach

---

## Service Files

- `services/media-security/service.py`
- `services/media-security/models.py`
- `services/media-security/test_media_security_service.py`

---

---

## Architectural Contract: MS-CONTENT-01 — Content Protection Enforcement (MS§10.5)

**Contract name:** MS-CONTENT-01
**Source authority:** Master Spec §10 rule 5: "Content protection must be enforced."
**Enforcement point:** `services/media-security/` — enforced at every content delivery session.

**Rule:** Content protection is active by default for all monetized and paid content. Three sub-rules apply:

1. **Default-on for paid content.** Any content flagged as monetized (associated with a paid plan, course with a fee, or commercial bundle) MUST have protection active by default. Protection is not opt-in for paid content — it is opt-out only for explicitly declared public content.

2. **No delivery without a protection session token.** Paid content MUST NOT be delivered without a valid protection session token issued by the media security service. Requests without a valid token MUST be rejected at the delivery layer.

3. **Public content opt-out is explicit and auditable.** Content designated as openly accessible (free public previews, open-course materials) may declare `protection_required: false`. This declaration MUST be an explicit, auditable field on the content record — not a default or an absence of configuration.

**Protection session token requirements (minimum):**
- Contains: `tenant_id`, `user_id`, `content_id`, `expiry`, optional IP binding
- Short-lived and non-transferable
- Revoked on entitlement change or security trigger (via CAP-SESSION-CONTROL)

**What a violation looks like:**
- A paid course whose content can be accessed directly via a media URL without a session token.
- A service delivering content based solely on user authentication, without a media security session gate.
- Content protection defaulting to `false` with operators required to turn it on.

**Why this rule exists:** MS§10 rule 5 states content protection must be enforced — not offered as an option. Without this named enforcement contract, protection gaps emerge as services handle media delivery ad hoc, creating revenue loss and piracy exposure.

---

## References

- Master Spec §5.11
- `docs/architecture/media_security_interface_contract.md`
- `docs/qc/B7P07_delivery_system_validation_report.md` — PASS 10/10
