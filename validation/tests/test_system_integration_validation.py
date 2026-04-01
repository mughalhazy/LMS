from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))


def _load_module(module_name: str, relative_path: str):
    module_path = ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


AcademyOpsModule = _load_module("academy_ops_system_validation_module", "services/academy-ops/service.py")
AnalyticsModule = _load_module("analytics_system_validation_module", "services/analytics-service/service.py")
MediaModule = _load_module("media_security_system_validation_module", "services/media-security/service.py")
WorkflowModule = _load_module("workflow_system_validation_module", "services/workflow-engine/service.py")
OfflineModule = _load_module("offline_sync_system_validation_module", "services/offline-sync/service.py")

from integrations.payments.adapters import MockSuccessAdapter
from integrations.payments.orchestration import PaymentOrchestrationService
from integrations.payments.router import PaymentProviderRouter
from services.commerce.models import ProductType
from services.commerce.service import CommerceService
from shared.models.media_policy import MediaAccessPolicy
from shared.validation import summarize_contract_validation, validate_service_dependency_contracts

AcademyOpsService = AcademyOpsModule.AcademyOpsService
UnifiedStudentProfile = AcademyOpsModule.UnifiedStudentProfile
WorkflowDefinition = WorkflowModule.WorkflowDefinition
WorkflowEngine = WorkflowModule.WorkflowEngine
WorkflowRule = WorkflowModule.WorkflowRule
WorkflowStep = WorkflowModule.WorkflowStep

AnalyticsService = AnalyticsModule.AnalyticsService
PlaybackContext = MediaModule.PlaybackContext
MediaSecurityService = MediaModule.MediaSecurityService
OfflineSyncService = OfflineModule.OfflineSyncService


class _ControlPlaneSpy:
    def __init__(self, *, enabled: bool) -> None:
        self.enabled = enabled
        self.calls: list[tuple[str, str]] = []

    def is_enabled(self, tenant_context, capability_id: str) -> bool:
        self.calls.append((tenant_context.tenant_id, capability_id))
        return self.enabled


def _bootstrap_commerce(*, country: str = "US") -> CommerceService:
    router = PaymentProviderRouter({country: "mock_success"}, [MockSuccessAdapter()])
    orchestration = PaymentOrchestrationService(router=router)
    return CommerceService(payment_orchestrator=orchestration, payment_country_code=country)


def test_system_contracts_have_no_broken_dependencies_or_control_plane_bypass() -> None:
    commerce = _bootstrap_commerce()
    academy = AcademyOpsService(commerce_service=commerce)
    workflow = WorkflowEngine(academy_ops_service=academy)

    contract_results = validate_service_dependency_contracts(
        payment_orchestrator=commerce._payment_orchestrator,
        sor_service=academy._sor,
        notification_orchestrator=workflow._notification_orchestrator,
    )
    summary = summarize_contract_validation(contract_results)

    assert all(summary.values())


def test_commerce_payments_and_academy_sor_interactions_are_consistent() -> None:
    commerce = _bootstrap_commerce()
    commerce.add_product(
        product_id="course-pro",
        tenant_id="tenant-a",
        title="Course Pro",
        price=Decimal("99.00"),
        currency="USD",
        type=ProductType.COURSE,
        capability_ids=["assessment.author"],
    )
    order, invoice = commerce.checkout_and_invoice_sync(
        session_id="sess-a",
        tenant_id="tenant-a",
        learner_id="learner-a",
        product_id="course-pro",
        idempotency_key="idem-a",
    )

    assert order.status.value == "reconciled"
    assert invoice.status.value == "pending"

    academy = AcademyOpsService(commerce_service=commerce)
    academy.register_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant-a",
            student_id="learner-a",
            full_name="Learner A",
            metadata={"country_code": "US", "segment_id": "academy"},
        )
    )
    academy.ingest_commerce_invoice(learner_id="learner-a", invoice_record=invoice)

    ledger = academy._sor.get_student_ledger(tenant_id="tenant-a", student_id="learner-a")
    assert any(entry.source_type == "invoice" and entry.source_ref == invoice.invoice_id for entry in ledger)


def test_workflow_communication_path_is_orchestrated_and_deduplicated() -> None:
    engine = WorkflowEngine()
    now = datetime(2026, 4, 1, 9, 0, tzinfo=timezone.utc)

    engine.register_workflow(
        WorkflowDefinition(
            workflow_id="wf_payment_reminder_validation",
            name="Payment Reminder Validation",
            enabled=True,
            rules=(WorkflowRule(rule_id="rule_due", trigger_type="payment.missed", required_context={"invoice_status": "overdue"}),),
            steps=(
                WorkflowStep(step_id="notify", step_type="notify", config={"message": "Please complete payment"}),
                WorkflowStep(step_id="create_action", step_type="action_item", config={"action_type": "payment_followup", "priority": "high"}),
            ),
        )
    )

    envelope = {
        "event_id": "evt-1",
        "event_type": "payment.missed",
        "timestamp": now.isoformat().replace("+00:00", "Z"),
        "tenant_id": "tenant-a",
        "correlation_id": "corr-1",
        "payload": {"country_code": "US", "segment_id": "academy", "invoice_status": "overdue"},
        "metadata": {"actor": {"user_id": "learner-a"}},
    }

    first = engine.handle_event_envelope(envelope)
    second = engine.handle_event_envelope(envelope)
    run = engine.run_due(now=now + timedelta(seconds=5))

    assert len(first["scheduled"]) == 2
    assert second["scheduled"] == []
    assert len(run["executed"]) == 2
    assert len(engine._notification_orchestrator._idempotent_send_log) == 1


def test_offline_media_flow_requires_control_plane_decision(tmp_path: Path) -> None:
    denied_cp = _ControlPlaneSpy(enabled=False)
    denied_media = MediaSecurityService(control_plane=denied_cp)
    denied_policy = MediaAccessPolicy(
        media_id="m-1",
        tenant_id="tenant-a",
        user_id="learner-a",
        capability_id="secure_media_delivery",
        token_expiry=datetime.now(timezone.utc) + timedelta(hours=1),
        offline_allowed=True,
    )
    denied_context = PlaybackContext(
        tenant_id="tenant-a",
        user_id="learner-a",
        media_id="m-1",
        session_id="s-1",
        channel="offline",
        device_id="dev-1",
        ip_address="10.1.1.1",
        offline_request=True,
    )
    denied_auth = denied_media.authorize_stream_access(policy=denied_policy, context=denied_context)

    assert denied_auth.decision == "deny"
    assert denied_cp.calls == [("tenant-a", "secure_media_delivery")]

    allowed_cp = _ControlPlaneSpy(enabled=True)
    allowed_media = MediaSecurityService(control_plane=allowed_cp)
    allowed_auth = allowed_media.authorize_stream_access(policy=denied_policy, context=denied_context)
    assert allowed_auth.decision == "allow"

    offline = OfflineSyncService(cache_root=tmp_path / "offline-cache", state_file=tmp_path / "offline-state" / "state.json")
    record = offline.record_offline_progress(
        tenant_id="tenant-a",
        student_id="learner-a",
        content_id="course-a",
        lesson_id="lesson-a",
        playback_position=120,
        completion_percent=80,
        reference_token="offline-ref-1",
    )
    offline.queue_progress_for_sync(record)
    sync_result = offline.sync_offline_progress()

    assert sync_result["succeeded"] == 1
    assert sync_result["pending"] == 0


def test_analytics_consumes_cross_service_outputs_without_duplicate_paths() -> None:
    commerce = _bootstrap_commerce()
    academy = AcademyOpsService(commerce_service=commerce)
    analytics = AnalyticsService()

    academy.register_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant-analytics",
            student_id="learner-analytics",
            full_name="Learner Analytics",
            metadata={"country_code": "US", "segment_id": "academy"},
        )
    )

    invoice = commerce.generate_academy_fee_invoice(
        tenant_id="tenant-analytics",
        learner_id="learner-analytics",
        fee_reference_id="fee-1",
        amount=Decimal("150.00"),
        fee_type="monthly_tuition",
    )
    academy.ingest_commerce_invoice(learner_id="learner-analytics", invoice_record=invoice)

    ledger_entries = tuple(academy._sor.get_student_ledger(tenant_id="tenant-analytics", student_id="learner-analytics"))
    owner_snapshot = analytics.compute_owner_economics(
        tenant_id="tenant-analytics",
        reporting_period="2026-04",
        ledger_entries=ledger_entries,
        commerce_invoices=tuple(commerce.billing._invoices.values()),
        academy_batches=tuple(),
        academy_branches=tuple(),
    )

    assert owner_snapshot.tenant_id == "tenant-analytics"
    assert owner_snapshot.metadata["sources"]["commerce_invoices"] == 1
    assert owner_snapshot.metadata["sources"]["ledger"] == len(ledger_entries)
