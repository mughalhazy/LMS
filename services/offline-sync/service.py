from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(Path(__file__).resolve().parent))


def _load_module(module_name: str, relative_path: str):
    module_path = ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_ContentOfflineModule = _load_module("offline_sync_content_module", "backend/services/content-service/offline.py")
_ModelsModule = _load_module("offline_sync_models_module", "services/offline-sync/models.py")
_MediaSecurityModule = _load_module("offline_sync_media_security_module", "services/media-security/service.py")


def _load_progress_module():
    package_name = "offline_sync_progress_src"
    package_path = ROOT / "backend/services/progress-service/src"
    package_spec = importlib.util.spec_from_file_location(
        package_name,
        package_path / "__init__.py",
        submodule_search_locations=[str(package_path)],
    )
    if package_spec is None or package_spec.loader is None:
        raise ImportError("Unable to initialize progress-service package")
    package_module = importlib.util.module_from_spec(package_spec)
    sys.modules[package_name] = package_module
    package_spec.loader.exec_module(package_module)

    module_spec = importlib.util.spec_from_file_location(
        f"{package_name}.progress_service",
        package_path / "progress_service.py",
    )
    if module_spec is None or module_spec.loader is None:
        raise ImportError("Unable to load progress_service module")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


_ProgressModule = _load_progress_module()
_OfflineProgressModel = _load_module("offline_progress_model", "shared/models/offline_progress.py")

OfflineContentManager = _ContentOfflineModule.OfflineContentManager
MediaSecurityService = _MediaSecurityModule.MediaSecurityService
OfflineDownloadContext = _MediaSecurityModule.OfflineDownloadContext
ProgressTrackingService = _ProgressModule.ProgressTrackingService
OfflineProgressRecord = _OfflineProgressModel.OfflineProgressRecord
OfflineProgressEnvelope = _ModelsModule.OfflineProgressEnvelope
SyncConflict = _ModelsModule.SyncConflict
SyncConflictType = _ModelsModule.SyncConflictType


class OfflineSyncService:
    """Offline downloads + progress sync with deterministic dedupe/conflict handling."""

    def __init__(
        self,
        *,
        cache_root: Path,
        state_file: Path,
        learning_service: ProgressTrackingService | None = None,
        system_of_record_service: Any | None = None,
        media_security_service: MediaSecurityService | None = None,
    ) -> None:
        self.downloads = OfflineContentManager(cache_root=cache_root)
        self.learning_service = learning_service or ProgressTrackingService()
        self.system_of_record_service = system_of_record_service
        self.media_security_service = media_security_service or MediaSecurityService()
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load_state()

    def download_for_offline(
        self,
        *,
        content_service: Any,
        tenant_id: str,
        content_id: str,
        requester_user_id: str,
        requester_roles: list[str],
    ) -> Any:
        return self.downloads.download_content(
            content_service=content_service,
            tenant_id=tenant_id,
            content_id=content_id,
            requester_user_id=requester_user_id,
            requester_roles=requester_roles,
        )

    def record_offline_progress(
        self,
        *,
        tenant_id: str,
        student_id: str,
        content_id: str,
        lesson_id: str,
        playback_position: int,
        completion_percent: float,
        local_timestamp: datetime | None = None,
        reference_token: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> OfflineProgressRecord:
        record = OfflineProgressRecord(
            offline_progress_id=str(uuid4()),
            student_id=student_id,
            tenant_id=tenant_id,
            content_id=content_id,
            lesson_id=lesson_id,
            playback_position=playback_position,
            completion_percent=completion_percent,
            local_timestamp=local_timestamp or datetime.now(timezone.utc),
            sync_status="queued",
            reference_token=reference_token or f"{tenant_id}:{student_id}:{content_id}:{lesson_id}",
            metadata=metadata or {},
        ).normalized()
        latest_payload = asdict(record)
        latest_payload["local_timestamp"] = record.local_timestamp.isoformat()
        self._state["latest_progress"][self._resume_key(record)] = latest_payload
        self._persist_state()
        return record

    def queue_progress_for_sync(self, record: OfflineProgressRecord) -> OfflineProgressRecord:
        normalized = record.normalized()
        if normalized.reference_token in self._state["applied_reference_tokens"]:
            return normalized

        existing_idx = next(
            (idx for idx, row in enumerate(self._state["pending"]) if row["reference_token"] == normalized.reference_token),
            None,
        )
        record_payload = asdict(normalized)
        record_payload["local_timestamp"] = normalized.local_timestamp.isoformat()
        if existing_idx is not None:
            existing = self._state["pending"][existing_idx]
            existing_time = datetime.fromisoformat(existing["local_timestamp"])
            if normalized.local_timestamp >= existing_time:
                self._state["pending"][existing_idx] = record_payload
        else:
            self._state["pending"].append(record_payload)

        self._persist_state()
        return normalized

    def list_pending_sync_records(self) -> list[OfflineProgressRecord]:
        rows = sorted(self._state["pending"], key=lambda row: (row["local_timestamp"], row["offline_progress_id"]))
        return [
            OfflineProgressRecord(
                **{
                    **row,
                    "local_timestamp": datetime.fromisoformat(row["local_timestamp"]),
                }
            )
            for row in rows
        ]

    def queue_progress(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        course_id: str,
        lesson_id: str,
        enrollment_id: str,
        completion_status: str,
        score: float | None,
        time_spent_seconds: int,
        attempt_count: int,
        timestamp: datetime | None = None,
        operation_id: str | None = None,
        package_expires_at: datetime | None = None,
    ) -> OfflineProgressEnvelope:
        metadata: dict[str, Any] = {"enrollment_id": enrollment_id, "score": score, "attempt_count": attempt_count}
        if package_expires_at is not None:
            metadata["package_expires_at"] = package_expires_at.astimezone(timezone.utc).isoformat()

        record = self.record_offline_progress(
            tenant_id=tenant_id,
            student_id=learner_id,
            content_id=course_id,
            lesson_id=lesson_id,
            playback_position=time_spent_seconds,
            completion_percent=100.0 if completion_status == "completed" else 50.0,
            local_timestamp=timestamp,
            reference_token=operation_id,
            metadata=metadata,
        )
        self.queue_progress_for_sync(record)
        return OfflineProgressEnvelope(
            operation_id=record.reference_token,
            tenant_id=tenant_id,
            learner_id=learner_id,
            course_id=course_id,
            lesson_id=lesson_id,
            enrollment_id=enrollment_id,
            completion_status=completion_status,
            score=score,
            time_spent_seconds=time_spent_seconds,
            attempt_count=attempt_count,
            timestamp=record.local_timestamp.isoformat(),
            package_expires_at=metadata.get("package_expires_at"),
        )

    def pending_operations(self) -> list[OfflineProgressEnvelope]:
        rows = self.list_pending_sync_records()
        return [
            OfflineProgressEnvelope(
                operation_id=row.reference_token,
                tenant_id=row.tenant_id,
                learner_id=row.student_id,
                course_id=row.content_id,
                lesson_id=row.lesson_id,
                enrollment_id=str(row.metadata.get("enrollment_id", "")),
                completion_status="completed" if row.completion_percent >= 100 else "in_progress",
                score=row.metadata.get("score"),
                time_spent_seconds=row.playback_position,
                attempt_count=int(row.metadata.get("attempt_count", 1)),
                timestamp=row.local_timestamp.isoformat(),
                package_expires_at=row.metadata.get("package_expires_at"),
                sync_attempts=int(row.metadata.get("sync_attempts", 0)),
                last_error=row.metadata.get("last_error"),
            )
            for row in rows
        ]

    def sync_progress(self, *, server_learning_service: ProgressTrackingService | None = None) -> dict[str, Any]:
        return self.sync_offline_progress(server_learning_service=server_learning_service)

    def sync_offline_progress(self, *, server_learning_service: ProgressTrackingService | None = None) -> dict[str, Any]:
        server = server_learning_service or self.learning_service
        pending = self.pending_operations()

        succeeded = 0
        conflicts = 0
        failed: list[dict[str, str]] = []
        still_pending: list[dict[str, Any]] = []
        self._state["last_sync_started_at"] = datetime.now(timezone.utc).isoformat()

        for op in pending:
            if op.operation_id in self._state["applied_reference_tokens"]:
                continue

            try:
                detected = self.detect_sync_conflicts(op=op, server=server)
                decision = self.resolve_sync_conflict(op=op, conflicts=detected)
                if decision["status"] == "dropped":
                    self.commit_sync_result(op=op, server=server, decision=decision)
                    conflicts += 1
                    continue

                self.commit_sync_result(op=op, server=server, decision=decision)
                succeeded += 1
            except Exception as exc:  # nosec - failure-safe retry queue
                op.sync_attempts += 1
                still_pending.append(
                    {
                        "offline_progress_id": str(uuid4()),
                        "student_id": op.learner_id,
                        "tenant_id": op.tenant_id,
                        "content_id": op.course_id,
                        "lesson_id": op.lesson_id,
                        "playback_position": op.time_spent_seconds,
                        "completion_percent": 100.0 if op.completion_status == "completed" else 50.0,
                        "local_timestamp": op.timestamp,
                        "sync_status": "failed",
                        "reference_token": op.operation_id,
                        "metadata": {
                            "enrollment_id": op.enrollment_id,
                            "score": op.score,
                            "attempt_count": op.attempt_count,
                            "package_expires_at": op.package_expires_at,
                            "sync_attempts": op.sync_attempts,
                            "last_error": str(exc),
                        },
                    }
                )
                failed.append({"operation_id": op.operation_id, "error": str(exc)})

        self._state["pending"] = still_pending
        self._state["applied_reference_tokens"] = sorted(set(self._state["applied_reference_tokens"]))
        self._persist_state()

        return {
            "attempted": len(pending),
            "succeeded": succeeded,
            "conflicts": conflicts,
            "failed": failed,
            "pending": len(still_pending),
        }

    def detect_sync_conflicts(self, *, op: OfflineProgressEnvelope, server: ProgressTrackingService) -> list[SyncConflict]:
        conflicts: list[SyncConflict] = []

        if op.operation_id in self._state["applied_reference_tokens"]:
            conflicts.append(
                SyncConflict(
                    conflict_type=SyncConflictType.DUPLICATE_PROGRESS_UPDATE,
                    strategy="drop_duplicate",
                    reason="operation already synced",
                )
            )
            return conflicts

        now = datetime.now(timezone.utc)
        if op.package_expires_at:
            expires_at = self._to_utc(op.package_expires_at)
            if expires_at and expires_at < now:
                conflicts.append(
                    SyncConflict(
                        conflict_type=SyncConflictType.INVALID_OR_EXPIRED_OFFLINE_PACKAGE,
                        strategy="drop_expired_package",
                        reason="offline package is expired and cannot be trusted",
                    )
                )
                return conflicts

        snapshot = server.get_learner_progress(op.tenant_id, op.learner_id)
        lesson = snapshot.get("lessons", {}).get(op.course_id, {}).get(op.lesson_id)
        if not lesson:
            return conflicts

        remote_attempt_count = int(lesson.get("attempt_count") or 0)
        remote_status = str(lesson.get("completion_status") or "")
        local_time = self._to_utc(op.timestamp)
        remote_time = self._to_utc(lesson.get("completed_at"))

        if remote_status == "completed" and ((remote_time and local_time and remote_time > local_time) or remote_attempt_count > op.attempt_count):
            conflicts.append(
                SyncConflict(
                    conflict_type=SyncConflictType.STALE_STATE_OVERWRITE,
                    strategy="server_wins",
                    reason="remote lesson state is newer than offline operation",
                )
            )

        remote_score = lesson.get("score")
        remote_time_spent = int(lesson.get("time_spent_seconds") or 0)
        if remote_status and (
            remote_attempt_count != op.attempt_count
            or remote_score != op.score
            or remote_time_spent != op.time_spent_seconds
        ):
            conflicts.append(
                SyncConflict(
                    conflict_type=SyncConflictType.SIMULTANEOUS_ONLINE_OFFLINE_UPDATE,
                    strategy="deterministic_merge",
                    reason="online and offline updates diverged for same lesson",
                )
            )

        return conflicts

    def resolve_sync_conflict(self, *, op: OfflineProgressEnvelope, conflicts: list[SyncConflict]) -> dict[str, Any]:
        _ = op
        types = {item.conflict_type for item in conflicts}
        if SyncConflictType.DUPLICATE_PROGRESS_UPDATE in types:
            return {"status": "dropped", "strategy": "duplicate_ignored"}
        if SyncConflictType.INVALID_OR_EXPIRED_OFFLINE_PACKAGE in types:
            return {"status": "dropped", "strategy": "expired_package_rejected"}
        if SyncConflictType.STALE_STATE_OVERWRITE in types:
            return {"status": "dropped", "strategy": "server_wins_stale_local"}

        if SyncConflictType.SIMULTANEOUS_ONLINE_OFFLINE_UPDATE in types:
            return {"status": "applied", "strategy": "deterministic_merge_local_replay"}

        return {"status": "applied", "strategy": "default_apply"}

    def commit_sync_result(
        self,
        *,
        op: OfflineProgressEnvelope,
        server: ProgressTrackingService,
        decision: dict[str, Any],
    ) -> None:
        if decision["status"] == "dropped":
            self._state["applied_reference_tokens"].append(op.operation_id)
            self._state["conflicts"].append(
                {
                    "operation_id": op.operation_id,
                    "tenant_id": op.tenant_id,
                    "learner_id": op.learner_id,
                    "course_id": op.course_id,
                    "lesson_id": op.lesson_id,
                    "strategy": decision["strategy"],
                    "at": datetime.now(timezone.utc).isoformat(),
                }
            )
            return

        if hasattr(server, "record_offline_progress"):
            server.record_offline_progress(
                tenant_id=op.tenant_id,
                learner_id=op.learner_id,
                course_id=op.course_id,
                lesson_id=op.lesson_id,
                enrollment_id=op.enrollment_id,
                completion_percent=100.0 if op.completion_status == "completed" else 50.0,
                playback_position=op.time_spent_seconds,
                reference_token=op.operation_id,
                attempt_count=op.attempt_count,
            )
        else:
            server.track_lesson_completion(
                tenant_id=op.tenant_id,
                learner_id=op.learner_id,
                course_id=op.course_id,
                lesson_id=op.lesson_id,
                enrollment_id=op.enrollment_id,
                completion_status=op.completion_status,
                score=op.score,
                time_spent_seconds=op.time_spent_seconds,
                attempt_count=op.attempt_count,
            )

        self._state["applied_reference_tokens"].append(op.operation_id)

        if self.system_of_record_service and hasattr(self.system_of_record_service, "commit_progress_sync_result"):
            self.system_of_record_service.commit_progress_sync_result(
                tenant_id=op.tenant_id,
                student_id=op.learner_id,
                course_id=op.course_id,
                lesson_id=op.lesson_id,
                operation_id=op.operation_id,
                completion_status=op.completion_status,
                score=op.score,
                time_spent_seconds=op.time_spent_seconds,
                attempt_count=op.attempt_count,
                source="offline-sync",
            )

    # ------------------------------------------------------------------ #
    # BC-OFFLINE-01 (CGAP-044) — Operator action queue                  #
    # ------------------------------------------------------------------ #

    _VALID_ACTION_TYPES = frozenset({
        "attendance_intent",
        "payment_record_intent",
        "note_intent",
        "fee_followup_intent",
        "approval_intent",
    })

    def queue_operator_action(
        self,
        *,
        action_type: str,
        payload: dict[str, Any],
        operator_id: str,
        tenant_id: str,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """BC-OFFLINE-01 (CGAP-044): queue an operational action intent for offline persistence.

        Stored in the local operator_action_queue and synced on reconnect in timestamp order
        before progress event sync. Each entry is idempotent via idempotency_key.
        """
        if action_type not in self._VALID_ACTION_TYPES:
            raise ValueError(
                f"unsupported action_type '{action_type}'. "
                f"Valid types: {sorted(self._VALID_ACTION_TYPES)}"
            )
        action_id = str(uuid4())
        key = idempotency_key or f"{operator_id}:{action_type}:{action_id}"
        if key in self._state.get("applied_action_ids", []):
            # Already applied — return a no-op acknowledgement
            return {"action_id": action_id, "status": "already_applied", "idempotency_key": key}

        entry: dict[str, Any] = {
            "action_id": action_id,
            "action_type": action_type,
            "payload": dict(payload),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "idempotency_key": key,
            "operator_id": operator_id,
            "tenant_id": tenant_id,
            "status": "pending",
        }
        self._state.setdefault("operator_action_queue", []).append(entry)
        self._persist_state()
        return entry

    def list_pending_operator_actions(self) -> list[dict[str, Any]]:
        """BC-OFFLINE-01 (CGAP-044): return all pending operator action intents sorted by created_at."""
        queue = self._state.get("operator_action_queue", [])
        return sorted(
            (entry for entry in queue if entry.get("status") == "pending"),
            key=lambda e: e["created_at"],
        )

    # ------------------------------------------------------------------ #
    # CGAP-045 — Operator action conflict detection + resolution         #
    # ------------------------------------------------------------------ #

    def detect_operator_action_conflicts(self, entry: dict[str, Any]) -> list[dict[str, Any]]:
        """CGAP-045: detect conflicts for an operator action intent before sync.

        Two conflict types are checked:
        1. duplicate — the same idempotency_key was already applied (safe to drop).
        2. conflicting_intent — a different action with the same action_type and entity_id
           was applied with a different decision value (e.g., present vs absent for same student/session).
           This requires operator review — never silently dropped.
        """
        conflicts: list[dict[str, Any]] = []

        # 1. Duplicate: same key already applied
        if entry["idempotency_key"] in self._state.get("applied_action_ids", []):
            conflicts.append({
                "conflict_type": "duplicate",
                "strategy": "drop_duplicate",
                "reason": "idempotency_key already applied",
            })
            return conflicts  # early return — no point checking further

        # 2. Conflicting intent: find an already-applied action with the same target but different decision
        payload = entry.get("payload", {})
        entity_id = str(payload.get("entity_id", payload.get("student_id", payload.get("batch_id", ""))))
        decision = str(payload.get("decision", payload.get("status", payload.get("attendance_status", ""))))

        if entity_id:
            for applied_key in self._state.get("applied_action_ids", []):
                # applied_action_ids stores keys; look through conflict log for prior resolutions
                pass
            # Check the operator_conflict_log for previously applied actions on same entity
            for prior in self._state.get("operator_conflict_log", []):
                if (
                    prior.get("action_type") == entry["action_type"]
                    and str(prior.get("entity_id", "")) == entity_id
                    and prior.get("applied", False)
                    and str(prior.get("decision", "")) != decision
                    and decision  # only flag if this entry actually carries a decision
                ):
                    conflicts.append({
                        "conflict_type": "conflicting_intent",
                        "strategy": "manual_review_required",
                        "reason": (
                            f"action_type='{entry['action_type']}' entity='{entity_id}' was already "
                            f"applied with decision='{prior['decision']}' but offline intent "
                            f"carries decision='{decision}'"
                        ),
                        "prior_action_id": prior.get("action_id"),
                        "prior_applied_at": prior.get("applied_at"),
                    })
                    break

        return conflicts

    def resolve_operator_action_conflict(
        self, entry: dict[str, Any], conflicts: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """CGAP-045: resolve a detected operator action conflict.

        Returns a decision dict with `status`:
        - "dropped"          → duplicate, safe to skip
        - "requires_review"  → conflicting intent; must surface to operator, never silently discard
        - "apply"            → no conflict, proceed normally
        """
        types = {c["conflict_type"] for c in conflicts}
        if "duplicate" in types:
            return {"status": "dropped", "strategy": "duplicate_ignored"}
        if "conflicting_intent" in types:
            detail = next(c for c in conflicts if c["conflict_type"] == "conflicting_intent")
            return {
                "status": "requires_review",
                "strategy": "manual_review_required",
                "resolution_prompt": (
                    f"Conflict: '{entry['action_type']}' for entity '{entry['payload'].get('entity_id', '')}' "
                    f"was already applied online with a different decision. "
                    f"Offline intent: '{detail.get('reason', '')}'. "
                    "Please review and re-apply the correct decision manually."
                ),
            }
        return {"status": "apply", "strategy": "default_apply"}

    def _record_operator_action_in_conflict_log(self, entry: dict[str, Any]) -> None:
        """CGAP-045: record an applied action in the conflict log for future conflict detection."""
        payload = entry.get("payload", {})
        entity_id = str(payload.get("entity_id", payload.get("student_id", payload.get("batch_id", ""))))
        decision = str(payload.get("decision", payload.get("status", payload.get("attendance_status", ""))))
        self._state.setdefault("operator_conflict_log", []).append({
            "action_id": entry["action_id"],
            "action_type": entry["action_type"],
            "entity_id": entity_id,
            "decision": decision,
            "applied": True,
            "applied_at": datetime.now(timezone.utc).isoformat(),
            "idempotency_key": entry["idempotency_key"],
        })

    def sync_operator_actions(self) -> dict[str, Any]:
        """BC-OFFLINE-01 (CGAP-044): replay pending operator actions in timestamp order on reconnect.

        CGAP-045: conflict detection runs before each action is dispatched.
        - Duplicates are silently dropped (safe deduplication).
        - Conflicting intents are surfaced to operator for manual resolution — never silently discarded.

        Must be called BEFORE sync_offline_progress() on reconnect.
        """
        pending = self.list_pending_operator_actions()
        applied = 0
        requires_resolution: list[dict[str, Any]] = []

        for entry in pending:
            if entry["idempotency_key"] in self._state.get("applied_action_ids", []):
                entry["status"] = "applied"
                applied += 1
                continue

            # CGAP-045: detect + resolve conflicts before dispatching
            conflicts = self.detect_operator_action_conflicts(entry)
            resolution = self.resolve_operator_action_conflict(entry, conflicts)

            if resolution["status"] == "dropped":
                entry["status"] = "applied"  # duplicate — treat as already-applied
                self._state.setdefault("applied_action_ids", []).append(entry["idempotency_key"])
                applied += 1
                continue

            if resolution["status"] == "requires_review":
                # Conflicting intent — surface to operator, never discard
                failed_entry = {
                    **entry,
                    "status": "conflict",
                    "conflict_strategy": resolution["strategy"],
                    "requires_resolution": True,
                    "resolution_prompt": resolution["resolution_prompt"],
                    "flagged_at": datetime.now(timezone.utc).isoformat(),
                }
                self._state.setdefault("failed_actions", []).append(failed_entry)
                entry["status"] = "conflict"
                requires_resolution.append(failed_entry)
                continue

            try:
                from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
                publish_event({
                    "event_type": "operator.action.sync",
                    "action_id": entry["action_id"],
                    "action_type": entry["action_type"],
                    "payload": entry["payload"],
                    "created_at": entry["created_at"],
                    "idempotency_key": entry["idempotency_key"],
                    "operator_id": entry["operator_id"],
                    "tenant_id": entry["tenant_id"],
                })
                entry["status"] = "applied"
                self._state.setdefault("applied_action_ids", []).append(entry["idempotency_key"])
                self._record_operator_action_in_conflict_log(entry)  # CGAP-045: track for future conflict detection
                applied += 1
            except Exception as exc:
                # Never discard — surface as resolution-required (BC-OFFLINE-01)
                failed_entry = {
                    **entry,
                    "status": "failed",
                    "error": str(exc),
                    "requires_resolution": True,
                    "resolution_prompt": (
                        f"Action '{entry['action_type']}' from {entry['created_at']} could not be synced "
                        f"(operator: {entry['operator_id']}). "
                        "Please review and re-apply manually or mark as resolved."
                    ),
                    "failed_at": datetime.now(timezone.utc).isoformat(),
                }
                self._state.setdefault("failed_actions", []).append(failed_entry)
                entry["status"] = "failed"
                requires_resolution.append(failed_entry)

        # Retain only pending entries in queue; applied/failed/conflict are archived
        self._state["operator_action_queue"] = [
            e for e in self._state.get("operator_action_queue", [])
            if e.get("status") == "pending"
        ]
        self._persist_state()

        return {
            "attempted": len(pending),
            "applied": applied,
            "requires_resolution": requires_resolution,
        }

    def get_failed_actions(self) -> list[dict[str, Any]]:
        """BC-OFFLINE-01 (CGAP-044): return operator actions that failed to sync and require resolution."""
        return list(self._state.get("failed_actions", []))

    def resolve_failed_action(self, *, action_id: str) -> bool:
        """BC-OFFLINE-01 (CGAP-044): mark a failed action as resolved by operator."""
        failed = self._state.get("failed_actions", [])
        for entry in failed:
            if entry["action_id"] == action_id:
                entry["status"] = "resolved"
                entry["requires_resolution"] = False
                self._state.setdefault("applied_action_ids", []).append(entry["idempotency_key"])
                self._persist_state()
                return True
        return False

    def sync_all(self, *, server_learning_service: Any = None) -> dict[str, Any]:
        """BC-OFFLINE-01 (CGAP-044): replay operator actions FIRST, then sync learning progress.

        This ordering guarantee (operator actions before progress events) is required by BC-OFFLINE-01
        — attendance/fee decisions must land before progress state is applied server-side.
        """
        operator_result = self.sync_operator_actions()
        progress_result = self.sync_offline_progress(server_learning_service=server_learning_service)
        return {"operator_actions": operator_result, "progress": progress_result}

    # ------------------------------------------------------------------
    # BC-FAIL-01: Offline manifest registration — MO-039 / Phase E
    # The media pipeline emits media.pipeline.offline_package_ready when
    # an offline package (MP4 + assets + manifest.json) is ready for download.
    # register_offline_manifest() consumes that event and stores the manifest
    # reference in local state so learners can see and download the package
    # without connectivity. Without this, offline packages build but are never
    # surfaced to the offline sync layer.
    # ------------------------------------------------------------------

    def register_offline_manifest(
        self,
        *,
        tenant_id: str,
        content_id: str,
        manifest_url: str,
        asset_count: int,
        total_size_bytes: int | None = None,
        expires_at: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Register an offline package manifest for learner download (BC-FAIL-01 / MO-039).

        Called when the media pipeline emits media.pipeline.offline_package_ready.
        Stores the manifest reference in offline state so it is included on the
        next sync and made available for offline access.

        Args:
            tenant_id: Tenant that owns this content.
            content_id: Content ID the offline package belongs to.
            manifest_url: Presigned URL to the manifest.json file.
            asset_count: Number of downloadable assets in the package.
            total_size_bytes: Uncompressed package size (optional — for UI display).
            expires_at: ISO datetime when presigned URLs expire (optional).
            metadata: Extra metadata from the pipeline job.

        Returns:
            Dict with registered manifest record.
        """
        manifest_record: dict[str, Any] = {
            "manifest_id": str(uuid4()),
            "tenant_id": tenant_id,
            "content_id": content_id,
            "manifest_url": manifest_url,
            "asset_count": asset_count,
            "total_size_bytes": total_size_bytes,
            "expires_at": expires_at,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "status": "available",
            **(metadata or {}),
        }

        # Append to offline_manifests list in state — seeded on load if absent
        self._state.setdefault("offline_manifests", [])
        # Deduplicate by content_id — replace existing if already registered
        existing = [m for m in self._state["offline_manifests"] if m.get("content_id") != content_id]
        existing.append(manifest_record)
        self._state["offline_manifests"] = existing
        self._persist_state()

        return manifest_record

    def list_offline_manifests(
        self,
        *,
        tenant_id: str | None = None,
        content_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Return registered offline manifests, optionally filtered (BC-FAIL-01 / MO-039)."""
        manifests: list[dict[str, Any]] = self._state.get("offline_manifests", [])
        if tenant_id:
            manifests = [m for m in manifests if m.get("tenant_id") == tenant_id]
        if content_id:
            manifests = [m for m in manifests if m.get("content_id") == content_id]
        return manifests

    def receive_pipeline_event(self, event: dict[str, Any]) -> bool:
        """Dispatch a media pipeline event to the appropriate handler (BC-FAIL-01 / MO-039).

        Accepts canonical event envelope dicts from the event bus.
        Supports: media.pipeline.offline_package_ready.

        Returns True if the event was handled, False if unrecognised.
        """
        event_type = event.get("event_type", "")
        payload = event.get("payload") or event  # support both envelope and flat dict

        if event_type == "media.pipeline.offline_package_ready":
            self.register_offline_manifest(
                tenant_id=str(payload.get("tenant_id") or event.get("tenant_id") or ""),
                content_id=str(payload.get("content_id", "")),
                manifest_url=str(payload.get("manifest_url", "")),
                asset_count=int(payload.get("asset_count", 0)),
                total_size_bytes=payload.get("total_size_bytes"),
                expires_at=payload.get("expires_at"),
                metadata={"source_event": event_type, "job_id": payload.get("job_id")},
            )
            return True

        return False

    def _load_state(self) -> dict[str, Any]:
        if not self.state_file.exists():
            return {
                "pending": [],
                "applied_reference_tokens": [],
                "conflicts": [],
                "latest_progress": {},
                "operator_action_queue": [],
                "applied_action_ids": [],
                "failed_actions": [],
                "operator_conflict_log": [],  # CGAP-045: tracks applied actions for conflict detection
                "offline_manifests": [],     # MO-039: registered offline package manifests
            }

        payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        pending_rows = payload.get("pending", [])
        payload["pending"] = [
            row
            if "reference_token" in row
            else {
                "offline_progress_id": str(uuid4()),
                "student_id": row["learner_id"],
                "tenant_id": row["tenant_id"],
                "content_id": row["course_id"],
                "lesson_id": row["lesson_id"],
                "playback_position": row["time_spent_seconds"],
                "completion_percent": 100.0 if row.get("completion_status") == "completed" else 50.0,
                "local_timestamp": row["timestamp"],
                "sync_status": "queued",
                "reference_token": row["operation_id"],
                "metadata": {
                    "enrollment_id": row.get("enrollment_id"),
                    "score": row.get("score"),
                    "attempt_count": row.get("attempt_count", 1),
                    "package_expires_at": row.get("package_expires_at"),
                },
            }
            for row in pending_rows
        ]
        payload.setdefault("applied_reference_tokens", payload.pop("applied_operation_ids", []))
        payload.setdefault("conflicts", [])
        payload.setdefault("latest_progress", {})
        # BC-OFFLINE-01 (CGAP-044): seed operator queue keys for existing state files
        payload.setdefault("operator_action_queue", [])
        payload.setdefault("applied_action_ids", [])
        payload.setdefault("failed_actions", [])
        # CGAP-045: conflict detection log for applied operator actions
        payload.setdefault("operator_conflict_log", [])
        return payload

    def _persist_state(self) -> None:
        tmp_file = self.state_file.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(self._state, indent=2, sort_keys=True), encoding="utf-8")
        tmp_file.replace(self.state_file)

    @staticmethod
    def _resume_key(record: OfflineProgressRecord) -> str:
        return f"{record.tenant_id}:{record.student_id}:{record.content_id}:{record.lesson_id}"

    @staticmethod
    def _to_utc(value: Any) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value)
            except ValueError:
                return None
        else:
            return None
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


__all__ = ["OfflineProgressEnvelope", "OfflineSyncService", "SyncConflict", "SyncConflictType"]
