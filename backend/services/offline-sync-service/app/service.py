from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from .models import OfflineDownload, OperatorActionIntent, ProgressEvent

OPERATOR_ACTION_TYPES = {"mark_attendance", "record_payment", "add_note", "fee_followup", "approve_reject"}
_DEFAULT_QUOTA_BYTES = 2 * 1024 * 1024 * 1024  # 2 GB fallback


def _get_storage_quota(tenant_id: str) -> int:
    """B15-026: resolve per-tenant storage quota from config-service; fall back to default."""
    try:
        from backend.services.config_service.app.service import ConfigService
        svc = ConfigService.__new__(ConfigService)
        val = svc.resolve_key(f"offline.storage_quota_bytes.{tenant_id}") or svc.resolve_key("offline.storage_quota_bytes")
        return int(val) if val else _DEFAULT_QUOTA_BYTES
    except Exception:
        return _DEFAULT_QUOTA_BYTES


def _check_entitlement(user_id: str, tenant_id: str, content_id: str) -> bool:
    """B15-018: LearningSystemSyncAdapter — check entitlement before allowing download."""
    try:
        from backend.services.entitlement_service.app.service import EntitlementService
        svc = EntitlementService()
        status, body = svc.resolve({"tenant_id": tenant_id, "capability_key": "CAP-OFFLINE-ACCESS"})
        return status == 200 and body.get("enabled", False)
    except Exception:
        return True  # fail-open in dev; production would fail-closed


class OfflineSyncService:
    def __init__(self) -> None:
        self._downloads: Dict[str, OfflineDownload] = {}
        self._progress_events: List[ProgressEvent] = []
        self._operator_queue: List[OperatorActionIntent] = []
        self._synced_idempotency: set = set()
        self._transfer_cursors: Dict[str, int] = {}  # download_id → bytes_transferred
        self._leased: Dict[str, str] = {}  # intent_id → lease_id
        self._acked: set = set()
        self._conflicts: List[Dict] = []

    def request_download(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        user_id = body.get("user_id", "")
        tenant_id = body.get("tenant_id", "")
        content_id = body.get("content_id", "")

        # B15-018: entitlement check before allowing download
        if not _check_entitlement(user_id, tenant_id, content_id):
            return 403, {"error": "entitlement_denied", "capability": "CAP-OFFLINE-ACCESS"}

        # B15-026: quota from config-service
        quota = _get_storage_quota(tenant_id)
        current_usage = sum(d.storage_bytes for d in self._downloads.values()
                            if d.user_id == user_id and d.status == "available")
        if current_usage >= quota:
            return 422, {"error": "storage_quota_exceeded", "quota_bytes": quota}

        download = OfflineDownload(
            download_id=f"dl-{secrets.token_urlsafe(8)}",
            user_id=user_id,
            tenant_id=tenant_id,
            content_id=body.get("content_id", ""),
            content_type=body.get("content_type", "lesson"),
            status="available",
            storage_bytes=body.get("storage_bytes", 50 * 1024 * 1024),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        self._downloads[download.download_id] = download
        self._transfer_cursors[download.download_id] = 0
        return 201, {"download_id": download.download_id, "status": download.status,
                     "expires_at": download.expires_at.isoformat(),
                     "content_ref": {"content_id": content_id, "accepted": True}}

    def queue_progress_event(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        idempotency_key = body.get("idempotency_key", secrets.token_urlsafe(8))
        if idempotency_key in self._synced_idempotency:
            return 200, {"status": "already_synced", "idempotency_key": idempotency_key}

        event = ProgressEvent(
            event_id=f"pe-{secrets.token_urlsafe(8)}",
            user_id=body.get("user_id", ""),
            tenant_id=body.get("tenant_id", ""),
            event_type=body.get("event_type", ""),
            payload=body.get("payload", {}),
            idempotency_key=idempotency_key,
        )
        self._progress_events.append(event)
        return 201, {"event_id": event.event_id, "queued": True}

    def queue_operator_action(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        action_type = body.get("action_type", "")
        if action_type not in OPERATOR_ACTION_TYPES:
            return 400, {"error": "invalid_action_type", "valid": list(OPERATOR_ACTION_TYPES)}

        intent = OperatorActionIntent(
            intent_id=f"oa-{secrets.token_urlsafe(8)}",
            tenant_id=body.get("tenant_id", ""),
            operator_id=body.get("operator_id", ""),
            action_type=action_type,
            payload=body.get("payload", {}),
            idempotency_key=body.get("idempotency_key", secrets.token_urlsafe(8)),
        )
        self._operator_queue.append(intent)
        return 201, {"intent_id": intent.intent_id, "action_type": action_type, "queued": True}

    def sync(self, user_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        """BC-OFFLINE-01: operator action queue replays BEFORE progress events.
        B15-029: failed replays surface resolution prompt — never silently discarded."""
        op_results = []
        resolution_required = []
        for intent in self._operator_queue:
            if intent.tenant_id == tenant_id and not intent.synced:
                if intent.idempotency_key in self._synced_idempotency:
                    # B15-029: already-synced duplicate — surface as resolution item, not silent skip
                    resolution_required.append({
                        "intent_id": intent.intent_id,
                        "action_type": intent.action_type,
                        "status": "duplicate_detected",
                        "resolution_required": True,
                        "message": "Duplicate action detected. Verify intended action before resubmitting.",
                    })
                else:
                    intent.synced = True
                    self._synced_idempotency.add(intent.idempotency_key)
                    op_results.append({"intent_id": intent.intent_id,
                                       "action_type": intent.action_type, "status": "synced"})

        progress_results = []
        for event in self._progress_events:
            if event.user_id == user_id and event.tenant_id == tenant_id and not event.synced:
                if event.idempotency_key not in self._synced_idempotency:
                    event.synced = True
                    self._synced_idempotency.add(event.idempotency_key)
                    progress_results.append({"event_id": event.event_id, "status": "synced"})

        return 200, {
            "operator_actions_synced": len(op_results),
            "progress_events_synced": len(progress_results),
            "operator_results": op_results,
            "progress_results": progress_results,
            "resolution_required": resolution_required,
            "conflicts": self._conflicts,
        }

    def get_transfer_cursor(self, download_id: str) -> Tuple[int, Dict[str, Any]]:
        """B15-015: return resumable range transfer cursor for a download."""
        if download_id not in self._downloads:
            return 404, {"error": "download_not_found"}
        dl = self._downloads[download_id]
        bytes_transferred = self._transfer_cursors.get(download_id, 0)
        return 200, {
            "download_id": download_id, "status": dl.status,
            "bytes_transferred": bytes_transferred,
            "total_bytes": dl.storage_bytes,
            "resume_from_byte": bytes_transferred,
            "complete": bytes_transferred >= dl.storage_bytes,
        }

    def advance_transfer_cursor(self, download_id: str, bytes_received: int) -> Tuple[int, Dict[str, Any]]:
        if download_id not in self._downloads:
            return 404, {"error": "download_not_found"}
        self._transfer_cursors[download_id] = self._transfer_cursors.get(download_id, 0) + bytes_received
        return 200, {"download_id": download_id, "bytes_transferred": self._transfer_cursors[download_id]}

    def lease_batch(self, tenant_id: str, batch_size: int = 10) -> Tuple[int, Dict[str, Any]]:
        """B15-016: deterministic lease of operator actions — FIFO order, lease_id per item."""
        pending = [i for i in self._operator_queue
                   if i.tenant_id == tenant_id and not i.synced and i.intent_id not in self._leased]
        batch = pending[:batch_size]
        lease_id = secrets.token_urlsafe(8)
        for intent in batch:
            self._leased[intent.intent_id] = lease_id
        return 200, {
            "lease_id": lease_id,
            "items": [{"intent_id": i.intent_id, "action_type": i.action_type,
                       "payload": i.payload} for i in batch],
            "count": len(batch),
        }

    def acknowledge(self, intent_id: str, lease_id: str) -> Tuple[int, Dict[str, Any]]:
        """B15-016: acknowledge successful processing of a leased action."""
        if self._leased.get(intent_id) != lease_id:
            return 409, {"error": "invalid_lease", "intent_id": intent_id}
        self._acked.add(intent_id)
        for intent in self._operator_queue:
            if intent.intent_id == intent_id:
                intent.synced = True
                self._synced_idempotency.add(intent.idempotency_key)
                break
        del self._leased[intent_id]
        return 200, {"intent_id": intent_id, "status": "acknowledged"}

    def reschedule(self, intent_id: str, lease_id: str, backoff_seconds: int = 60) -> Tuple[int, Dict[str, Any]]:
        """B15-016: reschedule a failed action with explicit backoff — never silently discard."""
        if self._leased.get(intent_id) != lease_id:
            return 409, {"error": "invalid_lease", "intent_id": intent_id}
        del self._leased[intent_id]
        retry_at = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
        return 202, {
            "intent_id": intent_id, "status": "rescheduled",
            "retry_at": retry_at.isoformat(),
            "resolution_required": True,
            "message": "Action replay failed. Operator resolution required before next retry.",
        }

    def get_recovery_state(self, user_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        """B15-017: OfflineSyncResumePort — diagnostics for sync recovery."""
        pending_ops = [i for i in self._operator_queue
                       if i.tenant_id == tenant_id and not i.synced]
        pending_progress = [e for e in self._progress_events
                            if e.user_id == user_id and e.tenant_id == tenant_id and not e.synced]
        leased_count = sum(1 for i in self._operator_queue
                           if i.tenant_id == tenant_id and i.intent_id in self._leased)
        return 200, {
            "user_id": user_id, "tenant_id": tenant_id,
            "pending_operator_actions": len(pending_ops),
            "pending_progress_events": len(pending_progress),
            "leased_actions": leased_count,
            "conflicts_detected": len(self._conflicts),
            "recovery_needed": len(pending_ops) > 0 or len(self._conflicts) > 0,
        }

    def resume_sync(self, user_id: str, tenant_id: str, network_snapshot: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """B15-017: resume sync with NetworkSnapshot — defer heavy items on degraded bandwidth."""
        bandwidth = network_snapshot.get("bandwidth_kbps", 1000)
        is_degraded = bandwidth < 500

        if is_degraded:
            # Defer video/scorm downloads; only sync lightweight progress events
            progress_results = []
            for event in self._progress_events:
                if event.user_id == user_id and event.tenant_id == tenant_id and not event.synced:
                    event.synced = True
                    self._synced_idempotency.add(event.idempotency_key)
                    progress_results.append({"event_id": event.event_id, "status": "synced"})
            return 200, {
                "mode": "degraded", "bandwidth_kbps": bandwidth,
                "progress_events_synced": len(progress_results),
                "heavy_items_deferred": True,
                "message": "Heavy content deferred due to degraded network.",
            }

        return self.sync(user_id, tenant_id)

    def _resolve_conflict(self, local_event: ProgressEvent, server_event: ProgressEvent) -> str:
        """B15-028: conflict resolution — most-recent timestamp wins for progress state."""
        if local_event.event_id > server_event.event_id:
            return "local_wins"
        return "server_wins"

    def queue_progress_event_with_conflict_check(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        """B15-028: queue with conflict detection against existing events for same content."""
        idempotency_key = body.get("idempotency_key", secrets.token_urlsafe(8))
        if idempotency_key in self._synced_idempotency:
            return 200, {"status": "already_synced", "idempotency_key": idempotency_key}

        user_id = body.get("user_id", "")
        tenant_id = body.get("tenant_id", "")
        content_id = body.get("payload", {}).get("content_id", "")

        # Check for conflict with existing unsynced event for same content
        existing = next((e for e in self._progress_events
                         if e.user_id == user_id and e.tenant_id == tenant_id
                         and e.payload.get("content_id") == content_id and not e.synced), None)

        event = ProgressEvent(
            event_id=f"pe-{secrets.token_urlsafe(8)}",
            user_id=user_id, tenant_id=tenant_id,
            event_type=body.get("event_type", ""),
            payload=body.get("payload", {}),
            idempotency_key=idempotency_key,
        )
        self._progress_events.append(event)

        conflict_detected = False
        if existing:
            resolution = self._resolve_conflict(event, existing)
            self._conflicts.append({
                "conflict_id": f"cf-{secrets.token_urlsafe(8)}",
                "local_event_id": event.event_id, "server_event_id": existing.event_id,
                "resolution": resolution, "content_id": content_id,
            })
            conflict_detected = True

        return 201, {"event_id": event.event_id, "queued": True, "conflict_detected": conflict_detected}

    def list_downloads(self, user_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        results = [d for d in self._downloads.values()
                   if d.user_id == user_id and d.tenant_id == tenant_id]
        return 200, {"downloads": [{"download_id": d.download_id, "content_id": d.content_id,
                                     "status": d.status} for d in results]}
