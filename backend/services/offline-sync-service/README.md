# offline-sync-service

Content download management, progress event queuing, offline operational action queue (BC-OFFLINE-01), and full port implementations for the offline-sync-interface-contract. Operator action intents sync before progress events on reconnect. Spec: `docs/specs/offline-sync-spec.md` (MS§5.12).

## Shared model

`backend/shared/models/offline_progress.py` — `OfflineProgressEvent`, `OfflineSyncConflict` (B15-027)

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/offline/downloads` | Request content download (entitlement-checked — B15-018) |
| GET | `/api/v1/offline/downloads/{id}/cursor` | Get resumable transfer cursor (B15-015) |
| POST | `/api/v1/offline/downloads/cursor` | Advance transfer cursor (B15-015) |
| POST | `/api/v1/offline/progress-events` | Queue progress event with conflict detection (B15-028) |
| POST | `/api/v1/offline/operator-actions` | Queue operator action |
| POST | `/api/v1/offline/operator-actions/lease` | Lease batch of actions — deterministic FIFO (B15-016) |
| POST | `/api/v1/offline/operator-actions/acknowledge` | Acknowledge successful action (B15-016) |
| POST | `/api/v1/offline/operator-actions/reschedule` | Reschedule failed action with backoff + resolution prompt (B15-016/029) |
| POST | `/api/v1/offline/sync` | Full sync — operator actions first, then progress events |
| POST | `/api/v1/offline/sync/resume` | Resume sync with NetworkSnapshot — defers heavy items on degraded bandwidth (B15-017) |
| GET | `/api/v1/offline/recovery-state` | Get sync recovery diagnostics (B15-017) |
| GET | `/health` | Health check |

## B15 fixes (2026-06-02)

- **B15-015**: `getTransferCursor()` + advance cursor — resumable range transfer per content download
- **B15-016**: `leaseBatch()`, `acknowledge()`, `reschedule()` — deterministic lease with explicit backoff
- **B15-017**: `resume_sync()` with NetworkSnapshot + `getRecoveryState()` — degraded bandwidth defers heavy items
- **B15-018**: `_check_entitlement()` — CAP-OFFLINE-ACCESS checked before any download accepted
- **B15-026**: Storage quota resolved from config-service per tenant; falls back to 2GB default
- **B15-027**: `shared/models/offline_progress.py` created at canonical path
- **B15-028**: Conflict resolution — most-recent event_id wins for same content_id; conflicts logged
- **B15-029**: BC-OFFLINE-01 — failed replays surface resolution prompt; never silently discarded
