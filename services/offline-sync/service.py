from __future__ import annotations

import importlib.util
import json
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[2]


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


@dataclass
class OfflineProgressEnvelope:
    operation_id: str
    tenant_id: str
    learner_id: str
    course_id: str
    lesson_id: str
    enrollment_id: str
    completion_status: str
    score: float | None
    time_spent_seconds: int
    attempt_count: int
    timestamp: str
    sync_attempts: int = 0
    last_error: str | None = None


class OfflineSyncService:
    """Offline downloads + progress sync with failure-safe retries and conflict resolution."""

    def __init__(
        self,
        *,
        cache_root: Path,
        state_file: Path,
        learning_service: ProgressTrackingService | None = None,
    ) -> None:
        self.downloads = OfflineContentManager(cache_root=cache_root)
        self.learning_service = learning_service or ProgressTrackingService()
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
        )
        self._state["pending"].append(asdict(envelope))
        self._persist_state()
        return envelope

    def pending_operations(self) -> list[OfflineProgressEnvelope]:
        rows = sorted(self._state["pending"], key=lambda row: (row["timestamp"], row["operation_id"]))
        return [OfflineProgressEnvelope(**row) for row in rows]

    def sync_progress(self, *, server_learning_service: ProgressTrackingService | None = None) -> dict[str, Any]:
        server = server_learning_service or self.learning_service
        pending = self.pending_operations()

        succeeded = 0
        conflicts = 0
        failed: list[dict[str, str]] = []
        still_pending: list[dict[str, Any]] = []

        for op in pending:
            if op.operation_id in self._state["applied_operation_ids"]:
                continue

            try:
                resolution = self._resolve_conflict(op=op, server=server)
                if resolution == "drop_as_conflict":
                    conflicts += 1
                    self._state["applied_operation_ids"].append(op.operation_id)
                    self._state["conflicts"].append(
                        {
                            "operation_id": op.operation_id,
                            "tenant_id": op.tenant_id,
                            "learner_id": op.learner_id,
                            "course_id": op.course_id,
                            "lesson_id": op.lesson_id,
                            "strategy": "server_wins_due_to_fresher_remote_update",
                            "at": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                    continue

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
                succeeded += 1
            except Exception as exc:  # nosec - failure-safe retry queue
                op.sync_attempts += 1
                row = asdict(op)
                row["last_error"] = str(exc)
                still_pending.append(row)
                failed.append({"operation_id": op.operation_id, "error": str(exc)})

        self._state["pending"] = still_pending
        self._state["applied_operation_ids"] = sorted(set(self._state["applied_operation_ids"]))
        self._persist_state()

        return {
            "attempted": len(pending),
            "succeeded": succeeded,
            "conflicts": conflicts,
            "failed": failed,
            "pending": len(still_pending),
        }

    def _resolve_conflict(self, *, op: OfflineProgressEnvelope, server: ProgressTrackingService) -> str:
        snapshot = server.get_learner_progress(op.tenant_id, op.learner_id)
        lesson = snapshot.get("lessons", {}).get(op.course_id, {}).get(op.lesson_id)
        if not lesson:
            return "apply"

        remote_attempt_count = int(lesson.get("attempt_count") or 0)
        remote_status = str(lesson.get("completion_status") or "")

        remote_completed_at = lesson.get("completed_at")
        local_time = datetime.fromisoformat(op.timestamp)
        if local_time.tzinfo is not None:
            local_time = local_time.astimezone(timezone.utc).replace(tzinfo=None)

        remote_completed_dt: datetime | None = None
        if isinstance(remote_completed_at, datetime):
            remote_completed_dt = remote_completed_at
        elif isinstance(remote_completed_at, str) and remote_completed_at:
            remote_completed_dt = datetime.fromisoformat(remote_completed_at)
        if remote_completed_dt and remote_completed_dt.tzinfo is not None:
            remote_completed_dt = remote_completed_dt.astimezone(timezone.utc).replace(tzinfo=None)

        if remote_completed_dt and remote_completed_dt > local_time and remote_status == "completed":
            return "drop_as_conflict"

        if remote_attempt_count > op.attempt_count and remote_status == "completed":
            return "drop_as_conflict"

        return "apply"

    def _load_state(self) -> dict[str, Any]:
        if not self.state_file.exists():
            return {"pending": [], "applied_operation_ids": [], "conflicts": []}

        payload = json.loads(self.state_file.read_text(encoding="utf-8"))
        payload.setdefault("pending", [])
        payload.setdefault("applied_operation_ids", [])
        payload.setdefault("conflicts", [])
        return payload

    def _persist_state(self) -> None:
        tmp_file = self.state_file.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(self._state, indent=2, sort_keys=True), encoding="utf-8")
        tmp_file.replace(self.state_file)


__all__ = ["OfflineProgressEnvelope", "OfflineSyncService"]
