from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/offline-sync/service.py"

spec = importlib.util.spec_from_file_location("offline_sync_test_module", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load offline-sync module")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

OfflineSyncService = module.OfflineSyncService
ProgressTrackingService = module.ProgressTrackingService


class _Metadata:
    def __init__(self, storage_uri: str, checksum_sha256: str, version: int = 1) -> None:
        self.storage_uri = storage_uri
        self.checksum_sha256 = checksum_sha256
        self.version = version


class _ContentServiceStub:
    def __init__(self, storage_uri: str, checksum_sha256: str, version: int = 1) -> None:
        self.metadata = _Metadata(storage_uri=storage_uri, checksum_sha256=checksum_sha256, version=version)

    def get_content(self, tenant_id: str, content_id: str, requester_user_id: str, requester_roles: list[str]):
        return {"metadata": self.metadata}


def test_offline_download_and_progress_sync_roundtrip(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    source.write_bytes(b"lesson-asset")

    import hashlib

    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    content_service = _ContentServiceStub(storage_uri=str(source), checksum_sha256=checksum)

    service = OfflineSyncService(
        cache_root=tmp_path / "offline-cache",
        state_file=tmp_path / "offline-state" / "state.json",
    )

    download = service.download_for_offline(
        content_service=content_service,
        tenant_id="tenant-a",
        content_id="content-1",
        requester_user_id="user-1",
        requester_roles=["learner"],
    )

    assert Path(download.local_uri).exists()

    service.queue_progress(
        tenant_id="tenant-a",
        learner_id="learner-1",
        course_id="course-1",
        lesson_id="lesson-1",
        enrollment_id="enr-1",
        completion_status="completed",
        score=90.0,
        time_spent_seconds=120,
        attempt_count=1,
    )

    result = service.sync_progress()
    assert result["succeeded"] == 1
    assert result["pending"] == 0


def test_conflict_resolution_server_wins_when_remote_is_fresher(tmp_path: Path) -> None:
    server = ProgressTrackingService()
    server.track_lesson_completion(
        tenant_id="tenant-a",
        learner_id="learner-2",
        course_id="course-1",
        lesson_id="lesson-2",
        enrollment_id="enr-2",
        completion_status="completed",
        score=95.0,
        time_spent_seconds=60,
        attempt_count=3,
    )

    service = OfflineSyncService(
        cache_root=tmp_path / "offline-cache",
        state_file=tmp_path / "offline-state" / "state.json",
        learning_service=server,
    )

    service.queue_progress(
        tenant_id="tenant-a",
        learner_id="learner-2",
        course_id="course-1",
        lesson_id="lesson-2",
        enrollment_id="enr-2",
        completion_status="completed",
        score=70.0,
        time_spent_seconds=30,
        attempt_count=1,
        timestamp=datetime(2024, 1, 1, tzinfo=timezone.utc),
    )

    result = service.sync_progress()
    assert result["conflicts"] == 1
    assert result["succeeded"] == 0
    assert result["pending"] == 0


def test_failure_safe_pending_is_retained_for_retry(tmp_path: Path) -> None:
    class _FailingServer:
        def track_lesson_completion(self, **kwargs):
            raise RuntimeError("temporary failure")

        def get_learner_progress(self, tenant_id: str, learner_id: str):
            return {"lessons": {}}

    service = OfflineSyncService(
        cache_root=tmp_path / "offline-cache",
        state_file=tmp_path / "offline-state" / "state.json",
    )

    service.queue_progress(
        tenant_id="tenant-a",
        learner_id="learner-3",
        course_id="course-1",
        lesson_id="lesson-3",
        enrollment_id="enr-3",
        completion_status="completed",
        score=88.0,
        time_spent_seconds=44,
        attempt_count=1,
    )

    result = service.sync_progress(server_learning_service=_FailingServer())
    assert result["succeeded"] == 0
    assert result["pending"] == 1

    reloaded = OfflineSyncService(
        cache_root=tmp_path / "offline-cache",
        state_file=tmp_path / "offline-state" / "state.json",
    )
    pending = reloaded.pending_operations()
    assert len(pending) == 1
    assert pending[0].sync_attempts == 1


def test_record_offline_progress_dedupes_by_reference_token(tmp_path: Path) -> None:
    service = OfflineSyncService(
        cache_root=tmp_path / "offline-cache",
        state_file=tmp_path / "offline-state" / "state.json",
    )

    first = service.record_offline_progress(
        tenant_id="tenant-a",
        student_id="learner-9",
        content_id="course-1",
        lesson_id="lesson-1",
        playback_position=10,
        completion_percent=10,
        reference_token="offline-ref-1",
    )
    service.queue_progress_for_sync(first)

    second = service.record_offline_progress(
        tenant_id="tenant-a",
        student_id="learner-9",
        content_id="course-1",
        lesson_id="lesson-1",
        playback_position=42,
        completion_percent=42,
        reference_token="offline-ref-1",
    )
    service.queue_progress_for_sync(second)

    pending = service.list_pending_sync_records()
    assert len(pending) == 1
    assert pending[0].playback_position == 42
