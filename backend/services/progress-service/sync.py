from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

from src.progress_service import ProgressTrackingService


@dataclass
class OfflineProgressOperation:
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


class OfflineProgressSyncEngine:
    """Tracks progress while offline and syncs it back to server safely."""

    def __init__(self, state_file: Path) -> None:
        self.state_file = state_file
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.local_service = ProgressTrackingService()
        self._state = self._load_state()

    def track_lesson_completion_offline(
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
    ) -> OfflineProgressOperation:
        op = OfflineProgressOperation(
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

        self._state["pending"].append(asdict(op))
        self._persist_state()

        self.local_service.track_lesson_completion(
            tenant_id=tenant_id,
            learner_id=learner_id,
            course_id=course_id,
            lesson_id=lesson_id,
            enrollment_id=enrollment_id,
            completion_status=completion_status,
            score=score,
            time_spent_seconds=time_spent_seconds,
            attempt_count=attempt_count,
        )
        return op

    def pending_operations(self) -> List[OfflineProgressOperation]:
        return [OfflineProgressOperation(**row) for row in self._state["pending"]]

    def sync_to_server(self, server_service: ProgressTrackingService) -> Dict[str, Any]:
        return self.sync_offline_progress(server_service)

    def sync_offline_progress(self, server_service: ProgressTrackingService) -> Dict[str, Any]:
        pending_rows = sorted(self._state["pending"], key=lambda row: (row["timestamp"], row["operation_id"]))
        applied_ids = set(self._state["applied_operation_ids"])

        succeeded = 0
        failed: list[dict[str, Any]] = []
        remaining: list[dict[str, Any]] = []

        for row in pending_rows:
            operation_id = row["operation_id"]
            if operation_id in applied_ids:
                continue

            conflicts = self.detect_sync_conflicts(row, server_service)
            decision = self.resolve_sync_conflict(conflicts)
            if decision["status"] == "drop":
                self.commit_sync_result(row, server_service, decision, applied_ids)
                continue

            try:
                self.commit_sync_result(row, server_service, decision, applied_ids)
                succeeded += 1
            except Exception as exc:  # nosec: keep unsynced operations for retry
                failed.append({"operation_id": operation_id, "error": str(exc)})
                remaining.append(row)

        self._state["pending"] = remaining
        self._state["applied_operation_ids"] = sorted(applied_ids)
        self._persist_state()

        return {
            "attempted": len(pending_rows),
            "succeeded": succeeded,
            "failed": failed,
            "pending": len(remaining),
        }

    def detect_sync_conflicts(self, row: Dict[str, Any], server_service: ProgressTrackingService) -> List[str]:
        conflicts: List[str] = []
        snapshot = server_service.get_learner_progress(row["tenant_id"], row["learner_id"])
        lesson = snapshot.get("lessons", {}).get(row["course_id"], {}).get(row["lesson_id"])
        if not lesson:
            return conflicts
        if int(lesson.get("attempt_count") or 0) > int(row["attempt_count"]):
            conflicts.append("stale_state_overwrite")
        if lesson.get("completion_status") and lesson.get("completion_status") != row["completion_status"]:
            conflicts.append("simultaneous_online_offline_updates")
        return conflicts

    def resolve_sync_conflict(self, conflicts: List[str]) -> Dict[str, str]:
        if "stale_state_overwrite" in conflicts:
            return {"status": "drop", "strategy": "server_wins"}
        return {"status": "apply", "strategy": "apply_or_merge"}

    def commit_sync_result(
        self,
        row: Dict[str, Any],
        server_service: ProgressTrackingService,
        decision: Dict[str, str],
        applied_ids: set[str],
    ) -> None:
        if decision["status"] == "drop":
            applied_ids.add(row["operation_id"])
            return

        server_service.track_lesson_completion(
                    tenant_id=row["tenant_id"],
                    learner_id=row["learner_id"],
                    course_id=row["course_id"],
                    lesson_id=row["lesson_id"],
                    enrollment_id=row["enrollment_id"],
                    completion_status=row["completion_status"],
                    score=row["score"],
                    time_spent_seconds=row["time_spent_seconds"],
                    attempt_count=row["attempt_count"],
        )
        applied_ids.add(row["operation_id"])

    def get_local_progress(self, tenant_id: str, learner_id: str) -> Dict[str, Any]:
        return self.local_service.get_learner_progress(tenant_id, learner_id)

    def _load_state(self) -> Dict[str, Any]:
        if not self.state_file.exists():
            return {"pending": [], "applied_operation_ids": []}
        return json.loads(self.state_file.read_text(encoding="utf-8"))

    def _persist_state(self) -> None:
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._state, indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(self.state_file)
