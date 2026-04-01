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
_OfflineProgressModel = _load_module("offline_progress_model", "shared/models/offline_progress.py")

OfflineContentManager = _ContentOfflineModule.OfflineContentManager
ProgressTrackingService = _ProgressModule.ProgressTrackingService
OfflineProgressRecord = _OfflineProgressModel.OfflineProgressRecord


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
    ) -> OfflineProgressEnvelope:
        record = self.record_offline_progress(
            tenant_id=tenant_id,
            student_id=learner_id,
            content_id=course_id,
            lesson_id=lesson_id,
            playback_position=time_spent_seconds,
            completion_percent=100.0 if completion_status == "completed" else 50.0,
            local_timestamp=timestamp,
            reference_token=operation_id,
            metadata={"enrollment_id": enrollment_id, "score": score, "attempt_count": attempt_count},
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
                sync_attempts=int(row.metadata.get("sync_attempts", 0)),
                last_error=row.metadata.get("last_error"),
            )
            for row in rows
        ]

    def sync_progress(self, *, server_learning_service: ProgressTrackingService | None = None) -> dict[str, Any]:
        server = server_learning_service or self.learning_service
        pending = self.pending_operations()

        succeeded = 0
        conflicts = 0
        failed: list[dict[str, str]] = []
        still_pending: list[dict[str, Any]] = []

        for op in pending:
            if op.operation_id in self._state["applied_reference_tokens"]:
                continue

            try:
                resolution = self._resolve_conflict(op=op, server=server)
                if resolution == "drop_as_conflict":
                    conflicts += 1
                    self._state["applied_reference_tokens"].append(op.operation_id)
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
            return {"pending": [], "applied_reference_tokens": [], "conflicts": [], "latest_progress": {}}

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
                },
            }
            for row in pending_rows
        ]
        payload.setdefault("applied_reference_tokens", payload.pop("applied_operation_ids", []))
        payload.setdefault("conflicts", [])
        payload.setdefault("latest_progress", {})
        return payload

    def _persist_state(self) -> None:
        tmp_file = self.state_file.with_suffix(".tmp")
        tmp_file.write_text(json.dumps(self._state, indent=2, sort_keys=True), encoding="utf-8")
        tmp_file.replace(self.state_file)

    @staticmethod
    def _resume_key(record: OfflineProgressRecord) -> str:
        return f"{record.tenant_id}:{record.student_id}:{record.content_id}:{record.lesson_id}"


__all__ = ["OfflineProgressEnvelope", "OfflineSyncService"]
