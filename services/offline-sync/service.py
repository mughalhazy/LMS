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

OfflineContentManager = _ContentOfflineModule.OfflineContentManager
ProgressTrackingService = _ProgressModule.ProgressTrackingService
OfflineProgressEnvelope = _ModelsModule.OfflineProgressEnvelope
SyncConflict = _ModelsModule.SyncConflict
SyncConflictType = _ModelsModule.SyncConflictType


class OfflineSyncService:
    """Offline downloads + progress sync with failure-safe retries and deterministic conflict handling."""

    def __init__(
        self,
        *,
        cache_root: Path,
        state_file: Path,
        learning_service: ProgressTrackingService | None = None,
        system_of_record_service: Any | None = None,
    ) -> None:
        self.downloads = OfflineContentManager(cache_root=cache_root)
        self.learning_service = learning_service or ProgressTrackingService()
        self.system_of_record_service = system_of_record_service
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
        envelope = OfflineProgressEnvelope(
            operation_id=operation_id or str(uuid4()),
            tenant_id=tenant_id,
            learner_id=learner_id,
            course_id=course_id,
            lesson_id=lesson_id,
            enrollment_id=enrollment_id,
            completion_status=completion_status,
            score=score,
            time_spent_seconds=time_spent_seconds,
            attempt_count=attempt_count,
            timestamp=(timestamp or datetime.now(timezone.utc)).isoformat(),
            package_expires_at=package_expires_at.isoformat() if package_expires_at else None,
        )
        self._state["pending"].append(asdict(envelope))
        self._persist_state()
        return envelope

    def pending_operations(self) -> list[OfflineProgressEnvelope]:
        rows = sorted(self._state["pending"], key=lambda row: (row["timestamp"], row["operation_id"]))
        return [OfflineProgressEnvelope(**row) for row in rows]

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
            conflict_list = self.detect_sync_conflicts(op=op, server=server)
            if conflict_list:
                decision = self.resolve_sync_conflict(op=op, conflicts=conflict_list)
                self.commit_sync_result(op=op, server=server, decision=decision)
                if decision["status"] == "applied":
                    succeeded += 1
                elif decision["status"] == "dropped":
                    conflicts += 1
                continue

            try:
                self.commit_sync_result(op=op, server=server, decision={"status": "applied", "strategy": "no_conflict"})
                succeeded += 1
            except Exception as exc:  # nosec - failure-safe retry queue
                op.sync_attempts += 1
                row = asdict(op)
                row["last_error"] = str(exc)
                still_pending.append(row)
                failed.append({"operation_id": op.operation_id, "error": str(exc)})

        self._state["pending"] = still_pending
        self._state["applied_operation_ids"] = sorted(set(self._state["applied_operation_ids"]))
        self._state["applied_dedupe_keys"] = sorted(set(self._state["applied_dedupe_keys"]))
        self._state["last_sync_finished_at"] = datetime.now(timezone.utc).isoformat()
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

        if op.operation_id in self._state["applied_operation_ids"] or op.dedupe_key in self._state["applied_dedupe_keys"]:
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
            self._state["applied_operation_ids"].append(op.operation_id)
            self._state["applied_dedupe_keys"].append(op.dedupe_key)
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
        self._state["applied_operation_ids"].append(op.operation_id)
        self._state["applied_dedupe_keys"].append(op.dedupe_key)

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

    def _load_state(self) -> dict[str, Any]:
        if not self.state_file.exists():
            return {
                "pending": [],
                "applied_operation_ids": [],
                "applied_dedupe_keys": [],
                "conflicts": [],
                "last_sync_started_at": None,
                "last_sync_finished_at": None,
            }

        payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        payload.setdefault("pending", [])
        payload.setdefault("applied_operation_ids", [])
        payload.setdefault("applied_dedupe_keys", [])
        payload.setdefault("conflicts", [])
        payload.setdefault("last_sync_started_at", None)
        payload.setdefault("last_sync_finished_at", None)
        return payload

    def _persist_state(self) -> None:
        tmp_file = self.state_file.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(self._state, indent=2, sort_keys=True), encoding="utf-8")
        tmp_file.replace(self.state_file)

    def _to_utc(self, value: str | datetime | None) -> datetime | None:
        if value is None:
            return None
        if isinstance(value, str):
            dt = datetime.fromisoformat(value)
        else:
            dt = value
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)


__all__ = ["OfflineProgressEnvelope", "OfflineSyncService", "SyncConflict", "SyncConflictType"]
