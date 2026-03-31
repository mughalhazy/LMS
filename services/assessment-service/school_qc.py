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


def _segment_behavior(config_service, segment_id: str) -> dict[str, bool]:
    from shared.models.config import ConfigResolutionContext, segment_behavior_from_effective_config

    effective = config_service.resolve(
        ConfigResolutionContext(tenant_id=f"tenant-{segment_id}", country_code="US", segment_id=segment_id)
    )
    segment_behavior = segment_behavior_from_effective_config(effective)
    return {
        "attendance_enabled": segment_behavior.attendance_enabled,
        "cohort_enabled": segment_behavior.cohort_enabled,
        "guardian_notifications_enabled": segment_behavior.guardian_notifications_enabled,
    }


def run_qc() -> tuple[int, dict[str, bool]]:
    config_module = _load_module("config_service", "services/config-service/service.py")
    course = _load_module("course_segment", "services/course-service/school_workflows.py")
    progress = _load_module("progress_segment", "services/progress-service/school_progress.py")
    assessment = _load_module("assessment_segment", "services/assessment-service/school_assessment.py")
    notify = _load_module("notify_segment", "services/notification-service/school_notifications.py")
    school_models = _load_module("school_models", "shared/models/school.py")

    from shared.models.config import ConfigLevel, ConfigOverride, ConfigScope

    config_service = config_module.ConfigService()
    config_service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.SEGMENT, scope_id="school"),
            capability_enabled={},
            behavior_tuning={
                "segment_behavior": {
                    "attendance_enabled": True,
                    "cohort_enabled": False,
                    "guardian_notifications_enabled": True,
                }
            },
        )
    )
    config_service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.SEGMENT, scope_id="academy"),
            capability_enabled={},
            behavior_tuning={
                "segment_behavior": {
                    "attendance_enabled": False,
                    "cohort_enabled": True,
                    "guardian_notifications_enabled": False,
                }
            },
        )
    )

    school_behavior = _segment_behavior(config_service, "school")
    academy_behavior = _segment_behavior(config_service, "academy")

    school_roster = course.SegmentCourseRoster(course_id="course-1", behavior_config=school_behavior)
    school_roster.enroll_student("stu-1")
    school_roster.add_guardian_link(school_models.StudentGuardianLink(student_id="stu-1", guardian_id="par-1"))
    school_roster.add_guardian_link(school_models.StudentGuardianLink(student_id="stu-1", guardian_id="par-2"))

    school_progress = progress.SegmentProgressService(behavior_config=school_behavior)
    school_progress.record_attendance_checkpoint(
        checkpoint_id="cp-1",
        student_id="stu-1",
        course_id="course-1",
        state="absent",
        period_key="2026-03-31-P1",
    )

    school_assessment = assessment.SegmentAssessmentService(behavior_config=school_behavior)
    perf_alert = school_assessment.record_score(student_id="stu-1", course_id="course-1", score_percent=42.0)

    school_notification = notify.SegmentNotificationService(behavior_config=school_behavior)
    attendance_notifications = school_notification.notify_guardians_for_attendance(
        guardian_ids=school_roster.guardians_for_student("stu-1"),
        student_id="stu-1",
        course_id="course-1",
        attendance_state="absent",
    )
    performance_notifications = school_notification.notify_guardians_for_performance_alert(
        guardian_ids=school_roster.guardians_for_student("stu-1"),
        alert=perf_alert,
    )

    academy_roster = course.SegmentCourseRoster(course_id="course-2", behavior_config=academy_behavior)
    academy_roster.enroll_student("stu-2")
    academy_roster.assign_student_to_cohort(student_id="stu-2", cohort_id="cohort-a")

    attendance_disabled_for_academy = False
    try:
        progress.SegmentProgressService(behavior_config=academy_behavior).record_attendance_checkpoint(
            checkpoint_id="cp-2",
            student_id="stu-2",
            course_id="course-2",
            state="present",
            period_key="2026-03-31-P2",
        )
    except RuntimeError as exc:
        attendance_disabled_for_academy = "attendance_enabled" in str(exc)

    checks = {
        "behavior_controlled_via_config": (
            school_behavior["attendance_enabled"]
            and school_behavior["guardian_notifications_enabled"]
            and academy_behavior["cohort_enabled"]
            and not academy_behavior["attendance_enabled"]
        ),
        "segment_config_applied_in_services": (
            len(school_progress.checkpoints_for_student(student_id="stu-1", course_id="course-1")) == 1
            and len(attendance_notifications) == 2
            and len(performance_notifications) == 2
            and academy_roster.cohort_members.get("cohort-a") == {"stu-2"}
            and attendance_disabled_for_academy
        ),
        "no_domain_hardcoding": all(token not in (ROOT / rel).read_text(encoding="utf-8").lower() for rel in (
            "services/course-service/school_workflows.py",
            "services/progress-service/school_progress.py",
            "services/assessment-service/school_assessment.py",
            "services/notification-service/school_notifications.py",
        ) for token in ('== "school"', '== "academy"', "segment_id ==")),
    }

    score = 10 if all(checks.values()) else 0
    return score, checks


if __name__ == "__main__":
    score, checks = run_qc()
    print({"score": score, "checks": checks})
    if score != 10:
        raise SystemExit(1)
