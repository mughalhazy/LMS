from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

from integrations.payments.adapters import MockSuccessAdapter
from integrations.payments.base_adapter import PaymentVerificationResult, TenantPaymentContext
from integrations.payments.orchestration import PaymentOrchestrationService
from integrations.payments.reconciliation import PaymentReconciliationEngine
from integrations.payments.router import PaymentProviderRouter
from services.commerce.catalog import ProductType
from services.commerce.service import CommerceService

ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "services/system-of-record/service.py"
_service_spec = importlib.util.spec_from_file_location("system_of_record_reconciliation_test_module", MODULE_PATH)
if _service_spec is None or _service_spec.loader is None:
    raise RuntimeError("Unable to load system-of-record module")
_service_module = importlib.util.module_from_spec(_service_spec)
sys.modules[_service_spec.name] = _service_module
_service_spec.loader.exec_module(_service_module)

SystemOfRecordService = _service_module.SystemOfRecordService
UnifiedStudentProfile = _service_module.UnifiedStudentProfile


class AlwaysFailStatusAdapter:
    provider_key = "unknown_adapter"

    def reconcile(self, *, payment_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        return PaymentVerificationResult(ok=False, status="failed", payment_id=payment_id, provider=self.provider_key, error="not_found")


class MockSuccessStatusAdapter:
    provider_key = "mock_success"

    def reconcile(self, *, payment_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        return PaymentVerificationResult(ok=True, status="verified", payment_id=payment_id, provider=self.provider_key)


def test_reconciliation_updates_order_invoice_and_ledger() -> None:
    router = PaymentProviderRouter({"US": "mock_success"}, [MockSuccessAdapter()])
    commerce = CommerceService(payment_orchestrator=PaymentOrchestrationService(router=router))
    commerce.add_product(
        product_id="p_recon",
        tenant_id="tenant_recon",
        type=ProductType.COURSE,
        title="Recon Course",
        price=Decimal("11.00"),
        currency="USD",
        capability_ids=["recommendation.basic"],
    )
    order, invoice = commerce.checkout_and_invoice_sync(
        session_id="sess_recon",
        tenant_id="tenant_recon",
        learner_id="student_recon",
        product_id="p_recon",
        idempotency_key="idem_recon",
    )

    sor = SystemOfRecordService()
    sor.upsert_student_profile(
        UnifiedStudentProfile(
            tenant_id="tenant_recon",
            student_id="student_recon",
            display_name="Re Con",
            email="recon@example.edu",
            country_code="US",
            segment_id="academy",
        )
    )

    engine = PaymentReconciliationEngine(
        adapters=[MockSuccessStatusAdapter()],
        commerce_target=commerce,
        ledger_target=sor,
        reconcile_interval_seconds=0,
    )
    engine.track_transaction(
        transaction_id=order.transaction_id or "txn_missing",
        tenant_id="tenant_recon",
        student_id="student_recon",
        provider="mock_success",
        payment_id=order.payment_id or "pay_missing",
        order_id=order.order_id,
        invoice_id=invoice.invoice_id,
        amount=order.amount,
        currency=order.currency,
        status="pending",
    )

    updated = engine.run_reconciliation_pass()

    assert updated[0].status == "verified"
    assert commerce.checkout.get_order(order.order_id).status.value == "reconciled"
    assert commerce.billing.get_invoice(invoice.invoice_id).state.value == "paid"
    assert sor.get_student_balance(tenant_id="tenant_recon", student_id="student_recon") == (order.amount * Decimal("-1"))
    assert engine.ensure_all_transactions_resolved() is True


def test_reconciliation_marks_unresolvable_transactions_as_failed() -> None:
    class CommerceTarget:
        def __init__(self) -> None:
            self.resolved = None

        def apply_reconciliation(self, *, order_id: str, invoice_id: str, payment_id: str, resolved: bool) -> None:
            self.resolved = resolved

    class LedgerTarget:
        def post_payment_to_ledger(self, *, tenant_id: str, student_id: str, payment_id: str, amount: Decimal, currency: str = "USD"):
            raise AssertionError("should not post failed payments")

    commerce_target = CommerceTarget()
    engine = PaymentReconciliationEngine(
        adapters=[AlwaysFailStatusAdapter()],
        commerce_target=commerce_target,
        ledger_target=LedgerTarget(),
        reconcile_interval_seconds=0,
        max_attempts=2,
    )
    engine.track_transaction(
        transaction_id="txn_unknown",
        tenant_id="tenant_x",
        student_id="student_x",
        provider="unknown_adapter",
        payment_id="pay_x",
        order_id="order_x",
        invoice_id="inv_x",
        amount=Decimal("5.00"),
        currency="USD",
        status="unknown",
    )

    engine.run_reconciliation_pass()
    final = engine.run_reconciliation_pass()[0]

    assert final.status == "failed"
    assert commerce_target.resolved is False
    assert engine.ensure_all_transactions_resolved() is True
