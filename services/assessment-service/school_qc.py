from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def _load_module(name: str, relative_path: str):
    file_path = ROOT / relative_path
    spec = importlib.util.spec_from_file_location(name, file_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run_qc() -> tuple[int, dict[str, bool]]:
    config_module = _load_module("config_service", "services/config-service/service.py")
    entitlement_module = _load_module("entitlement_service", "services/entitlement-service/service.py")
    runtime = _load_module("segment_runtime", "shared/segment_runtime.py")
    registry_module = _load_module("capability_registry", "services/capability-registry/service.py")

    from shared.models.config import ConfigLevel, ConfigOverride, ConfigScope
    from shared.models.capability import Capability
    from shared.utils.entitlement import TenantEntitlementContext

    config_service = config_module.ConfigService()
    entitlement = entitlement_module.EntitlementService(config_service=config_service)
    registry = registry_module.CapabilityRegistryService()

    for capability_id in (
        "course.roster.enroll",
        "course.roster.guardian_link.write",
        "progress.attendance.record",
        "assessment.score.record",
        "notification.guardian.attendance.send",
        "notification.guardian.performance.send",
    ):
        registry.register_capability(Capability(capability_id=capability_id, name=capability_id, description="qc", category="platform"))

    config_service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.SEGMENT, scope_id="school"),
            capability_enabled={
                "course.roster.enroll": True,
                "course.roster.guardian_link.write": True,
                "progress.attendance.record": True,
                "assessment.score.record": True,
                "notification.guardian.attendance.send": True,
                "notification.guardian.performance.send": True,
            },
            behavior_tuning={"segment_behavior": {"attendance_enabled": True, "cohort_enabled": False, "guardian_notifications_enabled": True}},
        )
    )

    tenant = TenantEntitlementContext(tenant_id="tenant-school", plan_type="free", country_code="US", segment_id="school")
    entitlement.upsert_tenant_context(tenant)
    context = runtime.SegmentRuntimeContext(tenant=tenant, correlation_id="qc-correlation")

    roster = runtime.SegmentCourseRoster(context=context, entitlement_service=entitlement, config_service=config_service)
    attendance = runtime.SegmentProgressService(context=context, entitlement_service=entitlement, config_service=config_service)
    assessment = runtime.SegmentAssessmentService(context=context, entitlement_service=entitlement, config_service=config_service)
    notification = runtime.SegmentNotificationService(context=context, entitlement_service=entitlement, config_service=config_service)

    roster.enroll_student("stu-1")
    roster.add_guardian_link(student_id="stu-1", guardian_id="par-1")
    roster.add_guardian_link(student_id="stu-1", guardian_id="par-2")

    attendance_event = attendance.record_attendance_checkpoint(
        checkpoint_id="cp-1", student_id="stu-1", course_id="course-1", state="absent", period_key="2026-03-31-P1"
    )
    alert_event = assessment.record_score(student_id="stu-1", course_id="course-1", score_percent=42.0)
    attendance_notifications = notification.notify_guardians(
        guardian_ids=sorted(roster.guardian_links["stu-1"]),
        category="attendance",
        message="Attendance update",
        student_id="stu-1",
        course_id="course-1",
    )
    performance_notifications = notification.notify_guardians(
        guardian_ids=sorted(roster.guardian_links["stu-1"]),
        category="performance",
        message="Performance update",
        student_id="stu-1",
        course_id="course-1",
    )

    standardized_keys = {"event_id", "event_type", "timestamp", "tenant_id", "correlation_id", "payload"}

    checks = {
        "behavior_controlled_via_config": len(attendance_notifications) == 2 and len(performance_notifications) == 2,
        "control_plane_only": entitlement.is_enabled(tenant, "assessment.score.record") is True,
        "events_standardized": standardized_keys.issubset(set(attendance_event.to_dict().keys())) and standardized_keys.issubset(set(alert_event.to_dict().keys())),
    }

    score = 10 if all(checks.values()) else 0
    return score, checks


if __name__ == "__main__":
    score, checks = run_qc()
    print({"score": score, "checks": checks})
    if score != 10:
        raise SystemExit(1)
