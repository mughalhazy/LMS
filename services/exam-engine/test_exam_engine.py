from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/exam-engine/service.py"
_service_spec = importlib.util.spec_from_file_location("exam_engine_test_module", MODULE_PATH)
if _service_spec is None or _service_spec.loader is None:
    raise RuntimeError("Unable to load exam engine module")
_service_module = importlib.util.module_from_spec(_service_spec)
sys.modules[_service_spec.name] = _service_module
_service_spec.loader.exec_module(_service_module)

ExamEngineService = _service_module.ExamEngineService
InMemoryAnalyticsIntegration = _service_module.InMemoryAnalyticsIntegration
InMemoryLearningIntegration = _service_module.InMemoryLearningIntegration
InMemoryProgressIntegration = _service_module.InMemoryProgressIntegration
TenantCapacityProfile = _service_module.TenantCapacityProfile


def test_sessions_are_tenant_isolated() -> None:
    service = ExamEngineService()
    s1 = service.start_session(tenant_id="tenant-a", learner_id="u1", exam_id="math")
    service.start_session(tenant_id="tenant-b", learner_id="u2", exam_id="science")

    assert service.tenant_metrics("tenant-a")["active_sessions"] == 1
    assert service.tenant_metrics("tenant-b")["active_sessions"] == 1

    service.submit_session(tenant_id="tenant-a", session_id=s1.session_id, score=88)

    assert service.tenant_metrics("tenant-a")["completed_sessions"] == 1
    assert service.tenant_metrics("tenant-b")["completed_sessions"] == 0


def test_load_handling_blocks_only_hot_tenant() -> None:
    service = ExamEngineService()
    service.register_tenant("tenant-hot", TenantCapacityProfile(max_active_sessions=2, shard_count=4))
    service.register_tenant("tenant-cold", TenantCapacityProfile(max_active_sessions=2, shard_count=4))

    service.start_session(tenant_id="tenant-hot", learner_id="u1", exam_id="x")
    service.start_session(tenant_id="tenant-hot", learner_id="u2", exam_id="x")

    try:
        service.start_session(tenant_id="tenant-hot", learner_id="u3", exam_id="x")
        raised = False
    except RuntimeError:
        raised = True

    assert raised is True

    session_cold = service.start_session(tenant_id="tenant-cold", learner_id="u9", exam_id="y")
    assert session_cold.tenant_id == "tenant-cold"


def test_submission_publishes_to_learning_analytics_and_progress() -> None:
    learning = InMemoryLearningIntegration()
    analytics = InMemoryAnalyticsIntegration()
    progress = InMemoryProgressIntegration()
    service = ExamEngineService(learning_integration=learning, analytics_integration=analytics, progress_integration=progress)

    session = service.start_session(tenant_id="tenant-1", learner_id="learner-1", exam_id="exam-1")
    submitted = service.submit_session(tenant_id="tenant-1", session_id=session.session_id, score=96)

    assert submitted.status == "submitted"
    assert len(learning.events) >= 1
    assert len(analytics.events) >= 1
    assert learning.events[-1]["tenant_id"] == "tenant-1"
    assert analytics.events[-1]["event_type"] == "exam.session.submitted"
    assert progress.events[-1]["event_type"] == "progress.exam.completed"


def test_shard_distribution_is_tenant_local_not_global_queue() -> None:
    service = ExamEngineService()
    service.register_tenant("tenant-1", TenantCapacityProfile(max_active_sessions=100, shard_count=2))
    service.register_tenant("tenant-2", TenantCapacityProfile(max_active_sessions=100, shard_count=2))

    for idx in range(10):
        service.start_session(tenant_id="tenant-1", learner_id=f"u{idx}", exam_id="exam")
    for idx in range(3):
        service.start_session(tenant_id="tenant-2", learner_id=f"v{idx}", exam_id="exam")

    t1_metrics = service.tenant_metrics("tenant-1")
    t2_metrics = service.tenant_metrics("tenant-2")

    assert sum(t1_metrics["shard_load"].values()) == 10
    assert sum(t2_metrics["shard_load"].values()) == 3


def test_prevents_conflicting_active_sessions_per_student_by_default() -> None:
    service = ExamEngineService()
    service.start_session(tenant_id="tenant-1", learner_id="student-1", exam_id="exam-1")

    try:
        service.start_session(tenant_id="tenant-1", learner_id="student-1", exam_id="exam-2")
        raised = False
    except RuntimeError:
        raised = True

    assert raised is True


def test_heartbeat_can_expire_session() -> None:
    service = ExamEngineService()
    session = service.create_exam_session(
        tenant_id="tenant-1",
        exam_id="exam-1",
        student_id="student-1",
        expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
    )
    service.start_exam_session(tenant_id="tenant-1", exam_session_id=session.exam_session_id)

    expired = service.heartbeat_exam_session(tenant_id="tenant-1", exam_session_id=session.exam_session_id)
    assert expired.status == "expired"
