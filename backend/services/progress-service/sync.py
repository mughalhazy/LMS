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
    occurred_at: str


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
        occurred_at: datetime | None = None,
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
            occurred_at=(occurred_at or datetime.now(timezone.utc)).isoformat(),
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
        pending_rows = sorted(self._state["pending"], key=lambda row: (row["occurred_at"], row["operation_id"]))
        applied_ids = set(self._state["applied_operation_ids"])

        succeeded = 0
        failed: list[dict[str, Any]] = []
        remaining: list[dict[str, Any]] = []

        for row in pending_rows:
            operation_id = row["operation_id"]
            if operation_id in applied_ids:
                continue

            try:
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
                succeeded += 1
                applied_ids.add(operation_id)
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
