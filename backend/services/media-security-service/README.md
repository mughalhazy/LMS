# media-security-service

Standalone media security service — deployment boundary separation for `media-service` security capabilities. Implements `docs/contracts/media-security-interface-contract.md` and `docs/specs/media-security-spec.md` as a dedicated FastAPI service. Created B15-014 (2026-06-02).

## Purpose

Separates media security concerns (entitlement gating, session control, anti-piracy) from the media pipeline into an independently deployable service, enabling different scaling and security policies.

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/media-security/playback/authorize` | Full entitlement-gated playback authorization (B15-011) |
| POST | `/api/v1/media-security/sessions/{session_id}/revoke` | Revoke media session (B15-024) |
| GET | `/api/v1/media-security/sessions` | List active sessions |
| POST | `/api/v1/media-security/anti-piracy/watermark-signal` | Handle piracy watermark signal (B15-013) |
| GET | `/api/v1/media-security/anti-piracy/anomaly-check` | Anomaly detection (B15-025) |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

## Capabilities implemented

- **CAP-SESSION-CONTROL**: max 2 concurrent sessions per user per tenant; explicit revocation on entitlement change or security trigger
- **CAP-ANTI-PIRACY-ENFORCEMENT**: 60 req/min rate limit; anomaly detection; `media.piracy.policy_violation` events on breach
- **EntitlementVerifier**: calls entitlement-service for `CAP-VIDEO-STREAMING` before granting playback
- **WatermarkHooks**: generates invisible per-user watermarks on grant; handles piracy signal callbacks
- **AntiPiracyHooks**: emits `media.piracy.policy_violation` bus events on rate/anomaly violations

## Layout

- `app/service.py` — `MediaSecurityService` implementing all security capabilities
- `app/main.py` — FastAPI routes

## Design references

`docs/contracts/media-security-interface-contract.md` | `docs/specs/media-security-spec.md`
