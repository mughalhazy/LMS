from __future__ import annotations

from dataclasses import dataclass

from .base_adapter import PaymentResult, normalize_tenant
from .router import PaymentProviderRouter


@dataclass
class Invoice:
    invoice_id: str
    tenant: str
    amount: int
    payment_status: str = "unpaid"
    payment_id: str | None = None


class InMemoryInvoiceStore:
    def __init__(self) -> None:
        self._invoices: dict[str, Invoice] = {}

    def create(self, tenant: str, amount: int) -> Invoice:
        invoice_id = f"inv_{tenant}_{len(self._invoices) + 1}"
        invoice = Invoice(invoice_id=invoice_id, tenant=tenant, amount=amount)
        self._invoices[invoice_id] = invoice
        return invoice

    def link_payment(self, invoice_id: str, payment_id: str | None, status: str) -> Invoice:
        invoice = self._invoices[invoice_id]
        invoice.payment_id = payment_id
        invoice.payment_status = status
        return invoice


class PaymentFlowService:
    """Generic payment flow that links payment result back to an invoice."""

    def __init__(self, router: PaymentProviderRouter, invoice_store: InMemoryInvoiceStore) -> None:
        self._router = router
        self._invoice_store = invoice_store

    def initiate_payment(self, amount: int, tenant: object) -> dict[str, str | int | None]:
        if amount <= 0:
            raise ValueError("amount must be greater than 0")

        tenant_context = normalize_tenant(tenant)
        invoice = self._invoice_store.create(tenant=tenant_context.tenant_id, amount=amount)
        adapter = self._router.resolve(tenant_context)
        result: PaymentResult = adapter.initiate_payment(
            amount=amount,
            tenant=tenant_context,
            invoice_id=invoice.invoice_id,
        )

        if result.ok:
            updated_invoice = self._invoice_store.link_payment(
                invoice_id=invoice.invoice_id,
                payment_id=result.payment_id,
                status="paid",
            )
            return {
                "status": "success",
                "provider": result.provider,
                "payment_id": result.payment_id,
                "invoice_id": updated_invoice.invoice_id,
                "invoice_payment_status": updated_invoice.payment_status,
                "amount": amount,
            }

        updated_invoice = self._invoice_store.link_payment(
            invoice_id=invoice.invoice_id,
            payment_id=None,
            status="payment_failed",
        )
        return {
            "status": "failure",
            "provider": result.provider,
            "payment_id": None,
            "error": result.error,
            "invoice_id": updated_invoice.invoice_id,
            "invoice_payment_status": updated_invoice.payment_status,
            "amount": amount,
        }
