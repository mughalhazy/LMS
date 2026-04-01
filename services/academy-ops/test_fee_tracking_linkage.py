from decimal import Decimal
import importlib.util
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from integrations.payment.adapters import MockSuccessAdapter
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
