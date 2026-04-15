# Offline Sync Spec

**Type:** Specification | **Date:** 2026-04-04 | **MS§:** §5.12 | **Service:** `services/offline-sync/`

---

## Capability Domain: §5.12 Offline Capabilities

Covers: offline access | local storage | sync engine | conflict resolution

---

## Service Boundary

The offline sync service manages the download, local storage, and re-synchronisation of learning content for users with unreliable connectivity. It enforces entitlement checks before allowing offline access and handles conflict resolution when online sync resumes.

---

## Capabilities Defined

### CAP-OFFLINE-ACCESS
- Entitlement-gated content download for offline consumption
- Download must verify: active enrollment, media security entitlement, storage quota
- Interface: `docs/architecture/offline_sync_interface_contract.md`

### CAP-LOCAL-STORAGE
- Manages the device-side storage envelope: what is cached, when it expires, how much space is used
- Respects tenant-level storage caps (from entitlement/config)

### CAP-SYNC-ENGINE
- Idempotent re-synchronisation of offline progress events when connectivity resumes
- Progress events generated offline are queued and replayed in order
- Deduplication: each progress event has a unique idempotency key
- Shared model: `shared/models/offline_progress.py`

### CAP-CONFLICT-RESOLUTION
- When online and offline progress states diverge, deterministic resolution applies:
  - Most-recent timestamp wins for progress state
  - All events are preserved in the append-only progress ledger
  - No data is discarded

---

## Service Files

- `services/offline-sync/service.py`
- `services/offline-sync/models.py`
- `services/offline-sync/test_offline_sync_service.py`

---

## References

- Master Spec §5.12, §7 (unreliable connectivity)
- `docs/architecture/offline_sync_interface_contract.md`
- `docs/qc/B7P07_delivery_system_validation_report.md` — PASS 10/10

---

## Behavioral Contract (BOS Overlay — 2026-04-04)

### BC-OFFLINE-01 — Operational Offline Behavior (BOS§7.2 / GAP-009)

**Rule:** The offline sync service MUST support offline OPERATIONAL actions — not only content download and learning progress sync. Operators must be able to take actions without connectivity, with those action intents stored locally and synced when connectivity resumes.

**Specification:**
The current capabilities (CAP-OFFLINE-ACCESS, CAP-LOCAL-STORAGE, CAP-SYNC-ENGINE, CAP-CONFLICT-RESOLUTION) cover learner-side content and progress. This contract adds the operational offline requirement:

**Required offline-capable operator actions:**
| Action | Local Behavior | Sync Behavior |
|---|---|---|
| Mark attendance | Store locally as `attendance_intent` event | Sync on reconnect via idempotency key |
| Record payment received | Store locally as `payment_record_intent` event | Sync on reconnect; SoR reconciles |
| Add note to student record | Store locally as `note_intent` event | Sync on reconnect; append-only |
| Initiate fee follow-up | Queue as `fee_followup_intent` | Dispatch when connectivity resumes |
| Approve/reject pending item | Store as `approval_intent` with timestamp | Sync on reconnect; timestamp-ordered |

**Implementation requirements:**
- The offline sync service must maintain a local `operator_action_queue` — an ordered, append-only log of pending operational action intents.
- Each action intent must carry: `action_type`, `payload`, `created_at`, `idempotency_key`, `operator_id`, `tenant_id`.
- On reconnect, the sync engine must replay the operator action queue in timestamp order before resuming progress event sync.
- Failed action replays (due to stale state) must surface a resolution prompt to the operator — they must never be silently discarded.
- Operators must receive clear offline-mode indicators in the UI and interaction channel, so they know their actions are queued but not yet applied.
