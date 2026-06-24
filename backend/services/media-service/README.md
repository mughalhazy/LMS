# Media Service

Media pipeline + playback security service. Implements LMS media lifecycle workflows and full entitlement-gated playback authorization per `docs/contracts/media-security-interface-contract.md` and `docs/specs/media-security-spec.md`.

## Scope

- **Media upload pipeline**: validates upload policy, stores raw source video, emits `video.uploaded`
- **Video processing**: transcodes to adaptive outputs (1080p/720p/480p), generates thumbnails, emits `video.transcoded`
- **CDN integration**: maps artifacts to CDN URLs with signed access, emits `video.published`
- **Playback security**: entitlement-gated authorization, watermarking, session control, anti-piracy (B15-011 to B15-025)

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/media/playback/authorize` | Full entitlement-gated playback authorization — returns token + watermark + session (B15-011) |
| POST | `/api/v1/media/sessions/{session_id}/revoke` | Revoke media session on entitlement change or security trigger (B15-024) |
| GET | `/api/v1/media/sessions` | List active sessions for user (B15-024) |
| POST | `/api/v1/media/anti-piracy/watermark-signal` | Receive watermark signal from piracy detection (B15-013) |
| GET | `/api/v1/media/anti-piracy/anomaly-check` | Detect anomalous access patterns (B15-025) |
| GET | `/health` | Health check |
| GET | `/metrics` | Service metrics |

## B15 fixes (2026-06-02)

- **B15-011**: `authorize_playback()` — full 5-step flow: EntitlementVerifier → rate limit → session control → watermark → token
- **B15-012**: `EntitlementVerifier` wired — checks `CAP-VIDEO-STREAMING` before granting playback
- **B15-013**: `WatermarkHooks` (`on_before_playback_grant`, `on_watermark_signal`) + `AntiPiracyHooks` (`on_policy_violation`) — emits `media.watermark.signal_detected` + `media.piracy.policy_violation`
- **B15-024**: `SessionController` — max 2 concurrent sessions per user per tenant; `revoke_session()` on entitlement/security trigger
- **B15-025**: `AntiPiracyEnforcer` — 60 req/min rate limit; anomaly detection at >30 req/min; violation emits bus event

## Standalone security service

For deployment boundary separation, see `backend/services/media-security-service/` (B15-014) — a standalone FastAPI service exposing the same security capabilities.

## Layout

- `app/security.py`: playback auth, session control, anti-piracy, watermark/piracy hooks
- `app/main.py`: FastAPI routes wiring security + pipeline
- `modules/media_pipeline/`: video processing pipeline
- `src/media_service/`: domain models, orchestration, CDN/transcoder adapters
