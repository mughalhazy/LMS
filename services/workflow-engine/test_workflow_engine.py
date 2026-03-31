from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.config import ConfigLevel, ConfigOverride, ConfigScope

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/workflow-engine/service.py"
_service_spec = importlib.util.spec_from_file_location("workflow_engine_test_module", MODULE_PATH)
if _service_spec is None or _service_spec.loader is None:
    raise RuntimeError("Unable to load workflow-engine module")
_service_module = importlib.util.module_from_spec(_service_spec)
sys.modules[_service_spec.name] = _service_module
_service_spec.loader.exec_module(_service_module)

WorkflowDefinition = _service_module.WorkflowDefinition
WorkflowEngine = _service_module.WorkflowEngine
WorkflowRule = _service_module.WorkflowRule
WorkflowStep = _service_module.WorkflowStep
WorkflowTriggerEvent = _service_module.WorkflowTriggerEvent


def test_trigger_rule_matching_scheduling_and_multi_step_execution() -> None:
    engine = WorkflowEngine()
    now = datetime(2026, 3, 31, 0, 0, tzinfo=timezone.utc)

    engine.register_workflow(
        WorkflowDefinition(
            workflow_id="wf_inactivity_nudge",
            name="Inactivity Nudge",
            enabled=True,
            rules=(
                WorkflowRule(
                    rule_id="rule_inactive_7d",
                    trigger_type="user_inactive",
                    required_context={"days_inactive": 7},
                ),
            ),
            steps=(
                WorkflowStep(
                    step_id="step_notify_user",
                    step_type="notify",
                    delay_seconds=0,
                    config={"message": "We noticed you have been away. Resume your course today."},
                ),
                WorkflowStep(
                    step_id="step_wait_24h",
                    step_type="wait",
                    delay_seconds=24 * 60 * 60,
                ),
                WorkflowStep(
                    step_id="step_escalate_manager",
                    step_type="escalate",
                    delay_seconds=24 * 60 * 60,
                    config={"target_role": "manager", "channel": "internal"},
                ),
            ),
        )
    )

    scheduled = engine.handle_trigger(
        WorkflowTriggerEvent(
            event_id="evt_001",
            tenant_id="tenant_1",
            country_code="US",
            segment_id="academy",
            trigger_type="user_inactive",
            actor_user_id="user_10",
            context={"days_inactive": 7},
            occurred_at=now,
        )
    )

    assert len(scheduled["scheduled"]) == 3
    assert any(trace["step"] == "workflow.matched" for trace in scheduled["trace"])

    first_run = engine.run_due(now=now + timedelta(minutes=1))
    assert len(first_run["executed"]) == 1
    assert first_run["executed"][0]["result"]["status"] == "sent"
    assert first_run["pending_count"] == 2

    second_run = engine.run_due(now=now + timedelta(hours=24, minutes=1))
    assert len(second_run["executed"]) == 2
    statuses = [item["result"]["status"] for item in second_run["executed"]]
    assert statuses == ["orchestrated", "orchestrated"]
    assert second_run["pending_count"] == 0


def test_config_service_can_disable_workflow_rule_set() -> None:
    engine = WorkflowEngine()
    engine._config_service.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.TENANT, scope_id="tenant_2"),
            behavior_tuning={"workflow_engine": {"disabled_workflows": ["wf_payment_reminder"]}},
        )
    )

    engine.register_workflow(
        WorkflowDefinition(
            workflow_id="wf_payment_reminder",
            name="Payment Reminder",
            enabled=True,
            rules=(
                WorkflowRule(
                    rule_id="rule_missed_payment",
                    trigger_type="missed_payment",
                    required_context={"invoice_status": "overdue"},
                ),
            ),
            steps=(
                WorkflowStep(
                    step_id="step_notify_payment",
                    step_type="notify",
                    config={"message": "Your invoice is overdue. Please complete payment."},
                ),
            ),
        )
    )

    scheduled = engine.handle_trigger(
        WorkflowTriggerEvent(
            event_id="evt_002",
            tenant_id="tenant_2",
            country_code="US",
            segment_id="academy",
            trigger_type="missed_payment",
            actor_user_id="user_20",
            context={"invoice_status": "overdue"},
        )
    )

    assert scheduled["scheduled"] == []
    assert all(entry["step"] != "workflow.matched" for entry in scheduled["trace"])


def test_event_envelope_trigger_and_cross_service_steps_execute() -> None:
    engine = WorkflowEngine()
    now = datetime(2026, 3, 31, 2, 0, tzinfo=timezone.utc)

    engine.register_workflow(
        WorkflowDefinition(
            workflow_id="wf_ops_and_payment",
            name="Ops + Payment",
            enabled=True,
            rules=(
                WorkflowRule(
                    rule_id="rule_fee_due",
                    trigger_type="payment.missed",
                    required_context={"invoice_status": "overdue"},
                ),
            ),
            steps=(
                WorkflowStep(
                    step_id="step_notify",
                    step_type="notify",
                    config={"message": "Your invoice is overdue."},
                ),
                WorkflowStep(
                    step_id="step_ops_qc",
                    step_type="academy_ops",
                    config={"operation": "run_qc_autofix"},
                ),
                WorkflowStep(
                    step_id="step_collect_payment",
                    step_type="payment",
                    config={"amount": 5000, "currency": "PKR", "invoice_id": "inv_5000"},
                ),
            ),
        )
    )

    scheduled = engine.handle_event_envelope(
        {
            "event_id": "evt_003",
            "event_type": "payment.missed",
            "timestamp": now.isoformat().replace("+00:00", "Z"),
            "tenant_id": "tenant_pk",
            "payload": {
                "country_code": "PK",
                "segment_id": "academy",
                "invoice_status": "overdue",
            },
            "metadata": {"actor": {"user_id": "user_55"}},
        }
    )

    assert len(scheduled["scheduled"]) == 3
    run = engine.run_due(now=now + timedelta(minutes=1))
    assert len(run["executed"]) == 3
    results = {item["step_id"]: item["result"] for item in run["executed"]}
    assert results["step_notify"]["status"] == "sent"
    assert results["step_ops_qc"]["status"] == "orchestrated"
    assert results["step_collect_payment"]["status"] in {"pending_verification", "verified"}
    assert run["pending_count"] == 0


def test_workflow_engine_qc_autofix_reports_baseline_guards() -> None:
    engine = WorkflowEngine()
    qc = engine.run_qc_autofix()

    assert qc["event_driven_triggers"] is True
    assert qc["rule_evaluation"] is True
    assert qc["multi_step_execution"] is True
    assert qc["notification_integration"] is True
    assert qc["academy_ops_integration"] is True
    assert qc["payments_integration"] is True
    assert qc["commerce_payments_contract"] is True
    assert qc["academy_sor_contract"] is True
    assert qc["workflow_notifications_contract"] is True
    assert qc["no_broken_dependencies"] is True
