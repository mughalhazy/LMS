from __future__ import annotations
import pytest
from app.service import WorkflowEngineService
from app.store import InMemoryWorkflowStore


def _svc() -> WorkflowEngineService:
    return WorkflowEngineService(InMemoryWorkflowStore())


def test_default_templates_seeded():
    svc = _svc()
    _, body = svc.list_templates()
    assert body["count"] == 6
    triggers = {t["event_trigger"] for t in body["templates"]}
    assert "enrollment.completed" in triggers
    assert "assessment.failed" in triggers


def test_default_templates_enabled_by_default():
    svc = _svc()
    _, body = svc.list_templates()
    assert all(t["enabled"] for t in body["templates"])


def test_trigger_enrollment_completed():
    svc = _svc()
    status, body = svc.trigger("enrollment.completed", "t1", {"learner_id": "u1"})
    assert status == 202
    assert body["triggered"] >= 1


def test_trigger_assessment_failed():
    svc = _svc()
    status, body = svc.trigger("assessment.failed", "t1", {"attempt_id": "a1"})
    assert status == 202
    assert body["triggered"] >= 1


def test_trigger_unknown_event():
    svc = _svc()
    _, body = svc.trigger("unknown.event", "t1", {})
    assert body["triggered"] == 0


def test_disable_template():
    svc = _svc()
    _, body = svc.enable_template("wf-enrollment-completed", False)
    assert body["enabled"] is False
    # Now trigger should not fire it
    _, result = svc.trigger("enrollment.completed", "t1", {})
    assert result["triggered"] == 0


def test_register_custom_template():
    svc = _svc()
    status, body = svc.register_template({
        "name": "Custom Flow", "event_trigger": "custom.event",
        "steps": [{"step_id": "s1", "action_type": "call_service",
                    "target_service": "my-service", "action_payload": {}}],
    })
    assert status == 200
    _, result = svc.trigger("custom.event", "t1", {})
    assert result["triggered"] == 1


def test_execution_recorded():
    svc = _svc()
    _, result = svc.trigger("enrollment.completed", "t1", {"learner_id": "u1"})
    exec_id = result["execution_ids"][0]
    status, body = svc.get_execution(exec_id)
    assert status == 200
    assert body["status"] == "completed"
    assert len(body["step_results"]) >= 1


def test_list_executions_tenant_scoped():
    svc = _svc()
    svc.trigger("enrollment.completed", "t1", {})
    svc.trigger("enrollment.completed", "t2", {})
    _, body = svc.list_executions("t1")
    assert all(e["tenant_id"] == "t1" for e in body["executions"])
