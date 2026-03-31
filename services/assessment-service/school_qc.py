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
    course = _load_module("course_school", "services/course-service/school_workflows.py")
    progress = _load_module("progress_school", "services/progress-service/school_progress.py")
    assessment = _load_module("assessment_school", "services/assessment-service/school_assessment.py")
    notify = _load_module("notify_school", "services/notification-service/school_notifications.py")
    school_models = _load_module("school_models", "shared/models/school.py")

    roster = course.SchoolCourseRoster(course_id="course-1")
    roster.enroll_student("stu-1")
    roster.add_guardian_link(school_models.StudentGuardianLink(student_id="stu-1", guardian_id="par-1"))
    roster.add_guardian_link(school_models.StudentGuardianLink(student_id="stu-1", guardian_id="par-2"))

    progress_service = progress.SchoolProgressService()
    progress_service.record_attendance_checkpoint(
        checkpoint_id="cp-1",
        student_id="stu-1",
        course_id="course-1",
        state="absent",
        period_key="2026-03-31-P1",
    )

    assessment_service = assessment.SchoolAssessmentService()
    perf_alert = assessment_service.record_score(student_id="stu-1", course_id="course-1", score_percent=42.0)

    notification_service = notify.SchoolNotificationService()
    attendance_notifications = notification_service.notify_guardians_for_attendance(
        guardian_ids=roster.guardians_for_student("stu-1"),
        student_id="stu-1",
        course_id="course-1",
        attendance_state="absent",
    )
    performance_notifications = notification_service.notify_guardians_for_performance_alert(
        guardian_ids=roster.guardians_for_student("stu-1"),
        alert=perf_alert,
    )

    checks = {
        "school_workflows_work": len(progress_service.checkpoints_for_student(student_id="stu-1", course_id="course-1")) == 1,
        "parent_notification_logic_works": len(attendance_notifications) == 2 and len(performance_notifications) == 2,
        "no_domain_leakage": all(n.category in {"attendance", "performance"} for n in attendance_notifications + performance_notifications),
    }

    score = 10 if all(checks.values()) else sum(3 for ok in checks.values() if ok)
    return score, checks


if __name__ == "__main__":
    score, checks = run_qc()
    print({"score": score, "checks": checks})
    if score != 10:
        raise SystemExit(1)
