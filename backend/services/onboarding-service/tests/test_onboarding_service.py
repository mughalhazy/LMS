from __future__ import annotations
import pytest
from app.service import OnboardingService


def _svc() -> OnboardingService:
    return OnboardingService()


def test_start_onboarding():
    svc = _svc()
    status, body = svc.start_onboarding({"tenant_id": "t1", "segment_type": "corp",
                                          "plan_type": "basic", "country_code": "PK"})
    assert status == 201
    assert body["status"] == "in_progress"
    assert "config_bootstrapped" in [body["current_step"]]


def test_idempotent_start():
    svc = _svc()
    svc.start_onboarding({"tenant_id": "t1", "segment_type": "corp", "plan_type": "basic"})
    status, body = svc.start_onboarding({"tenant_id": "t1", "segment_type": "corp", "plan_type": "basic"})
    assert status == 200
    assert "already_started" in body["message"]


def test_complete_steps_to_done():
    svc = _svc()
    _, session = svc.start_onboarding({"tenant_id": "t1", "segment_type": "corp",
                                        "plan_type": "basic", "country_code": "US"})
    sid = session["session_id"]
    remaining = [s for s in ["config_bootstrapped", "capabilities_activated",
                               "admin_provisioned", "guided_flow_started",
                               "first_capability_activated"]]
    for step in remaining:
        _, body = svc.complete_step(sid, step)
    assert body["status"] == "completed"
    assert body["progress_pct"] == 100


def test_wrong_step_rejected():
    svc = _svc()
    _, session = svc.start_onboarding({"tenant_id": "t1"})
    status, body = svc.complete_step(session["session_id"], "wrong_step")
    assert status == 422
    assert "wrong_step" in body["error"]


def test_get_defaults_non_null():
    svc = _svc()
    status, body = svc.get_defaults("corp", "enterprise", "PK")
    assert status == 200
    # BC-ONBOARD-01: every default must be non-null
    for d in body["defaults"]:
        assert d["default_value"] is not None


def test_get_defaults_all_areas_covered():
    svc = _svc()
    _, body = svc.get_defaults("school", "basic", "US")
    areas = {d["area"] for d in body["defaults"]}
    required = {"branding", "locale", "feature_flags", "notification_templates",
                 "automation_workflows", "fee_reminder_schedule", "attendance_rules",
                 "compliance_settings", "report_schedule"}
    assert required.issubset(areas)
