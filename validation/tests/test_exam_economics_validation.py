from __future__ import annotations

import importlib.util
import sys
from datetime import date
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


ExamModule = _load_module("exam_engine_validation_module", "services/exam-engine/service.py")
AcademyModule = _load_module("academy_ops_validation_module", "services/academy-ops/service.py")
AnalyticsModule = _load_module("analytics_validation_module", "services/analytics-service/service.py")
EnterpriseModule = _load_module("enterprise_validation_module", "services/enterprise-control/service.py")

from integrations.payments.adapters import MockSuccessAdapter
from services.commerce.service import CommerceService
from integrations.payments.orchestration import PaymentOrchestrationService
from integrations.payments.router import PaymentProviderRouter

ExamEngineService = ExamModule.ExamEngineService
InMemoryCapabilityIntegration = ExamModule.InMemoryCapabilityIntegration
TenantCapacityProfile = ExamModule.TenantCapacityProfile
AcademyOpsService = AcademyModule.AcademyOpsService
Batch = AcademyModule.Batch
Branch = AcademyModule.Branch
TeacherAssignment = AcademyModule.TeacherAssignment
UnifiedStudentProfile = AcademyModule.UnifiedStudentProfile
AnalyticsService = AnalyticsModule.AnalyticsService
EnterpriseControlService = EnterpriseModule.EnterpriseControlService
IdentityContext = EnterpriseModule.IdentityContext


def _bootstrap_ops(tenant_id: str) -> tuple[AcademyOpsService, CommerceService]:
    router = PaymentProviderRouter({"US": "mock_success"}, [MockSuccessAdapter()])
    commerce = CommerceService(payment_orchestrator=PaymentOrchestrationService(router=router))
    return AcademyOpsService(commerce_service=commerce), commerce


def test_e2e_student_exam_session_is_tenant_isolated_and_burst_safe() -> None:
    exam = ExamEngineService(
        capability_integration=InMemoryCapabilityIntegration(
            enabled_capabilities={
                "tenant_a": {"assessment.attempt"},
                "tenant_b": {"assessment.attempt"},
            }
        )
    )
    exam.register_tenant("tenant_a", TenantCapacityProfile(max_active_sessions=1, shard_count=2, burst_queue_limit=1))
    exam.register_tenant("tenant_b", TenantCapacityProfile(max_active_sessions=1, shard_count=2, burst_queue_limit=0))

    first = exam.start_session(tenant_id="tenant_a", learner_id="s-1", exam_id="exam-core")
    queued = exam.start_session(tenant_id="tenant_a", learner_id="s-2", exam_id="exam-core")
    assert queued.status == "queued"

    second_tenant = exam.start_session(tenant_id="tenant_b", learner_id="s-3", exam_id="exam-core")
    assert second_tenant.tenant_id == "tenant_b"

    exam.submit_session(tenant_id="tenant_a", session_id=first.session_id, score=93)
    metrics = exam.tenant_metrics("tenant_a")
    assert metrics["completed_sessions"] == 1
    assert metrics["active_sessions"] == 1
    assert metrics["status_counts"]["queued"] == 0
    assert len(exam.tenant_audit_log("tenant_a")) >= 3


def test_teacher_owned_batch_revenue_share_and_audit_are_consistent() -> None:
    tenant_id = "tenant_econ"
    learner_id = "student_1"
    batch_id = "batch_1"
    teacher_id = "teacher_1"
    service, commerce = _bootstrap_ops(tenant_id)

    service.register_student_profile(
        UnifiedStudentProfile(
            tenant_id=tenant_id,
            student_id=learner_id,
            full_name="Economics Learner",
            metadata={"country_code": "US", "segment_id": "academy"},
        )
    )
    service.create_branch(Branch(tenant_id=tenant_id, branch_id="branch_1", name="Main", code="MAIN", location="Remote"))
    service.create_batch(
        Batch(
            tenant_id=tenant_id,
            branch_id="branch_1",
            batch_id=batch_id,
            academy_id="academy_1",
            title="Revenue Batch",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 6, 1),
            learner_ids=(learner_id,),
        )
    )
    service.assign_teacher_to_batch(TeacherAssignment(tenant_id=tenant_id, branch_id="branch_1", batch_id=batch_id, teacher_id=teacher_id))
    service.mark_batch_teacher_owned(tenant_id=tenant_id, branch_id="branch_1", batch_id=batch_id, teacher_id=teacher_id)
    service.assign_revenue_share(tenant_id=tenant_id, batch_id=batch_id, teacher_id=teacher_id, revenue_share_percent=Decimal("35"))

    invoice = commerce.generate_academy_fee_invoice(
        tenant_id=tenant_id,
        learner_id=learner_id,
        fee_reference_id="f1",
        amount=Decimal("200.00"),
        fee_type="one_time_batch",
    )
    service.ingest_commerce_invoice_for_batch(learner_id=learner_id, batch_id=batch_id, invoice_record=invoice)

    payouts = service.teacher_payouts(tenant_id=tenant_id, batch_id=batch_id)
    assert len(payouts) == 1
    assert payouts[0].payout_amount == Decimal("70.00")
    assert commerce._teacher_revenue_share_records[0]["tenant_id"] == tenant_id

    ledger = service._sor.get_student_ledger(tenant_id=tenant_id, student_id=learner_id)
    assert any(entry.source_type == "teacher_payout" for entry in ledger)


def test_owner_economics_snapshot_uses_real_records() -> None:
    tenant_id = "tenant_owner"
    learner_id = "s_owner"
    service, commerce = _bootstrap_ops(tenant_id)
    analytics = AnalyticsService()

    service.register_student_profile(
        UnifiedStudentProfile(tenant_id=tenant_id, student_id=learner_id, full_name="Owner Learner", metadata={"country_code": "US", "segment_id": "academy"})
    )
    service.create_branch(Branch(tenant_id=tenant_id, branch_id="branch_owner", name="Owner", code="OWN", location="HQ", metadata={"estimated_overhead": "20"}))
    service.create_batch(
        Batch(
            tenant_id=tenant_id,
            branch_id="branch_owner",
            batch_id="batch_owner",
            academy_id="academy_owner",
            title="Owner Cohort",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 5, 1),
            learner_ids=(learner_id,),
            metadata={"estimated_cost": "60"},
        )
    )
    invoice = commerce.generate_academy_fee_invoice(tenant_id=tenant_id, learner_id=learner_id, fee_reference_id="owner_1", amount=Decimal("180.00"), fee_type="monthly_tuition")
    service.ingest_commerce_invoice(learner_id=learner_id, invoice_record=invoice)

    snapshot = analytics.compute_owner_economics(
        tenant_id=tenant_id,
        reporting_period="2026-04",
        ledger_entries=tuple(service._sor.get_student_ledger(tenant_id=tenant_id, student_id=learner_id)),
        commerce_invoices=tuple(commerce.billing._invoices.values()),
        academy_batches=(service._batches[(tenant_id, "batch_owner")],),
        academy_branches=(service._branches[(tenant_id, "branch_owner")],),
    )
    assert snapshot.revenue_per_student == Decimal("180.00")
    assert snapshot.total_cash_in == Decimal("0")
    assert snapshot.estimated_profit == Decimal("100.00")
    assert snapshot.metadata["sources"]["ledger"] >= 1


def test_cross_institution_assignment_stays_permission_safe_and_tenant_separated() -> None:
    target_tenant = "tenant_target"
    home_tenant = "tenant_home"
    teacher_id = "teacher_x"

    enterprise = EnterpriseControlService()
    enterprise.set_role_permissions(tenant_id=home_tenant, role="admin", permissions={"teacher.network.manage"})
    enterprise.set_role_permissions(tenant_id=target_tenant, role="admin", permissions={"academy.teacher_assignment.cross_institution"})

    home_admin = IdentityContext(tenant_id=home_tenant, actor_id="admin_home", roles=("admin",))
    target_admin = IdentityContext(tenant_id=target_tenant, actor_id="admin_target", roles=("admin",))

    enterprise.link_teacher_to_external_tenant(
        identity=home_admin,
        home_tenant_id=home_tenant,
        teacher_id=teacher_id,
        external_tenant_id=target_tenant,
    )

    service, _commerce = _bootstrap_ops(target_tenant)
    service._enterprise_control = enterprise
    service.create_branch(Branch(tenant_id=target_tenant, branch_id="branch_1", name="B1", code="B1", location="Remote"))
    service.create_batch(
        Batch(
            tenant_id=target_tenant,
            branch_id="branch_1",
            batch_id="batch_1",
            academy_id="academy_1",
            title="Cross",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 5, 1),
        )
    )

    assigned = service.assign_teacher_cross_institution(
        assignment=TeacherAssignment(tenant_id=target_tenant, branch_id="branch_1", batch_id="batch_1", teacher_id=teacher_id),
        enterprise_identity=target_admin,
        home_tenant_id=home_tenant,
        payout_rate=Decimal("0.25"),
    )
    assert assigned.teacher_id == teacher_id

    wrong_identity = IdentityContext(tenant_id="wrong_tenant", actor_id="hacker", roles=("admin",))
    try:
        enterprise.assign_teacher_cross_institution(
            identity=wrong_identity,
            target_tenant_id=target_tenant,
            home_tenant_id=home_tenant,
            teacher_id=teacher_id,
            branch_id="branch_1",
            batch_id="batch_2",
            payout_rate=0.1,
        )
        raised = False
    except PermissionError:
        raised = True
    assert raised is True
