from decimal import Decimal
import importlib.util
import sys
from datetime import date
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from integrations.payments.adapters import MockSuccessAdapter
from integrations.payments.orchestration import PaymentOrchestrationService
from integrations.payments.router import PaymentProviderRouter
from services.commerce.service import CommerceService

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/academy-ops/service.py"
_service_spec = importlib.util.spec_from_file_location("academy_ops_fee_tracking_test_module", MODULE_PATH)
if _service_spec is None or _service_spec.loader is None:
    raise RuntimeError("Unable to load academy-ops module")
_service_module = importlib.util.module_from_spec(_service_spec)
sys.modules[_service_spec.name] = _service_module
_service_spec.loader.exec_module(_service_module)

AcademyOpsService = _service_module.AcademyOpsService
UnifiedStudentProfile = _service_module.UnifiedStudentProfile
Batch = _service_module.Batch
Branch = _service_module.Branch
TeacherAssignment = _service_module.TeacherAssignment


def test_fee_tracking_is_linked_to_commerce_and_system_of_record() -> None:
    router = PaymentProviderRouter({"US": "mock_success"}, [MockSuccessAdapter()])
    commerce = CommerceService(payment_orchestrator=PaymentOrchestrationService(router=router))
    service = AcademyOpsService(commerce_service=commerce)
    service.register_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_fee",
            student_id="learner_fee",
            full_name="Fee Student",
            metadata={"country_code": "US", "segment_id": "academy"},
        )
    )

    service.assign_fee_plan_to_student(
        tenant_id="tenant_fee",
        learner_id="learner_fee",
        fee_plan_id="plan_monthly",
        fee_type="monthly_tuition",
        total_amount=Decimal("300.00"),
        installment_count=3,
    )
    invoice = service.generate_student_fee_invoice(
        tenant_id="tenant_fee",
        learner_id="learner_fee",
        installment_index=1,
    )
    service.mark_fee_due(
        tenant_id="tenant_fee",
        learner_id="learner_fee",
        invoice_id=invoice.invoice_id,
        overdue=True,
    )
    service.mark_fee_paid(
        tenant_id="tenant_fee",
        learner_id="learner_fee",
        invoice_id=invoice.invoice_id,
        payment_id="pay_fee_1",
        amount=Decimal("100.00"),
    )

    status = service.get_student_fee_status(tenant_id="tenant_fee", learner_id="learner_fee")
    assert status["fee_plan"]["fee_type"] == "monthly_tuition"
    assert status["invoice_status"][invoice.invoice_id] == "paid"
    assert status["overdue"] is False

    profile = service._sor.get_student_profile(tenant_id="tenant_fee", student_id="learner_fee")
    assert profile is not None
    assert profile.metadata["fee.overdue"] == "false"
    assert commerce.billing.get_invoice(invoice.invoice_id) is not None
    ledger = service._sor.get_student_ledger(tenant_id="tenant_fee", student_id="learner_fee")
    assert len(ledger) >= 4


def test_teacher_owned_batch_revenue_share_is_attributed_and_auditable() -> None:
    router = PaymentProviderRouter({"US": "mock_success"}, [MockSuccessAdapter()])
    commerce = CommerceService(payment_orchestrator=PaymentOrchestrationService(router=router))
    service = AcademyOpsService(commerce_service=commerce)
    tenant_id = "tenant_teacher_owned"
    learner_id = "learner_teacher_owned"
    batch_id = "batch_teacher_owned"
    teacher_id = "teacher_owner_1"

    service.register_student_profile(
        UnifiedStudentProfile(
            tenant_id=tenant_id,
            student_id=learner_id,
            full_name="Teacher Owned Learner",
            metadata={"country_code": "US", "segment_id": "academy"},
        )
    )
    service.create_branch(
        Branch(tenant_id=tenant_id, branch_id="branch_to", name="TO", code="TO", location="remote")
    )
    service.create_batch(
        Batch(
            tenant_id=tenant_id,
            branch_id="branch_to",
            batch_id=batch_id,
            academy_id="academy_to",
            title="Teacher Owned Batch",
            start_date=date(2026, 4, 1),
            end_date=date(2026, 7, 1),
            learner_ids=(learner_id,),
        )
    )
    service.assign_teacher_to_batch(
        TeacherAssignment(tenant_id=tenant_id, branch_id="branch_to", batch_id=batch_id, teacher_id=teacher_id)
    )
    service.mark_batch_teacher_owned(
        tenant_id=tenant_id,
        branch_id="branch_to",
        batch_id=batch_id,
        teacher_id=teacher_id,
        payout_schedule="weekly",
    )
    service.assign_revenue_share(
        tenant_id=tenant_id,
        batch_id=batch_id,
        teacher_id=teacher_id,
        revenue_share_percent=Decimal("40"),
        payout_schedule="weekly",
    )

    commerce_invoice = commerce.generate_academy_fee_invoice(
        tenant_id=tenant_id,
        learner_id=learner_id,
        fee_reference_id="teacher_owned_fee_1",
        amount=Decimal("120.00"),
        fee_type="one_time_batch",
    )
    service.ingest_commerce_invoice_for_batch(learner_id=learner_id, batch_id=batch_id, invoice_record=commerce_invoice)
    economics = service.calculate_teacher_batch_earnings(tenant_id=tenant_id, batch_id=batch_id)
    owned_batches = service.list_teacher_owned_batches(tenant_id=tenant_id, teacher_id=teacher_id)

    assert economics.revenue_share_percent == Decimal("40.00")
    assert economics.earnings_to_date == Decimal("48.00")
    assert economics.pending_payout_amount == Decimal("48.00")
    assert [batch.batch_id for batch in owned_batches] == [batch_id]
    assert len(commerce._teacher_revenue_share_records) == 1
    assert commerce._teacher_revenue_share_records[0]["invoice_id"] == commerce_invoice.invoice_id

    ledger = service._sor.get_student_ledger(tenant_id=tenant_id, student_id=learner_id)
    assert any(entry.source_type == "teacher_payout" for entry in ledger)
