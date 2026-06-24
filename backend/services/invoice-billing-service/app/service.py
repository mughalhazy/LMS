from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .models import AuditTrailEntry, BillingAccount, BillingRecord, Invoice, InvoiceLine
from .store import InMemoryBillingStore

VALID_INVOICE_TYPES = {"recurring", "one_time", "adjustment", "credit_note"}
VALID_LINE_TYPES = {"subscription_fee", "usage", "one_time_item", "tax", "discount", "adjustment"}
STATE_MACHINE = {
    "draft": {"validated"},
    "validated": {"issued"},
    "issued": {"paid", "overdue", "voided", "disputed"},
    "disputed": {"issued"},
    "overdue": {"voided", "written_off"},
    "paid": set(),
    "voided": set(),
    "written_off": set(),
}


class BillingService:
    def __init__(self, store: InMemoryBillingStore) -> None:
        self.store = store

    def create_billing_account(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        account = BillingAccount(
            billing_account_id=self.store.new_id("ba"),
            tenant_id=body.get("tenant_id", ""),
            customer_id=body.get("customer_id", ""),
            billing_timezone=body.get("billing_timezone", "UTC"),
            currency=body.get("currency", "USD"),
            invoice_delivery_preferences=body.get("invoice_delivery_preferences", {}),
        )
        self.store.save_account(account)
        return 201, self._serialize_account(account)

    def get_billing_account(self, billing_account_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        account = self.store.get_account(billing_account_id)
        if not account or account.tenant_id != tenant_id:
            return 404, {"error": "billing_account_not_found"}
        return 200, self._serialize_account(account)

    def create_invoice(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        invoice_type = body.get("invoice_type", "one_time")
        if invoice_type not in VALID_INVOICE_TYPES:
            return 400, {"error": "invalid_invoice_type"}

        account = self.store.get_account(body.get("billing_account_id", ""))
        if not account:
            return 404, {"error": "billing_account_not_found"}

        lines_data = body.get("lines", [])
        lines = []
        subtotal = 0.0
        for ld in lines_data:
            amount = float(ld.get("quantity", 1)) * float(ld.get("unit_price", 0))
            line = InvoiceLine(
                invoice_line_id=self.store.new_id("ln"),
                invoice_id="",
                line_type=ld.get("line_type", "one_time_item"),
                source_ref=ld.get("source_ref"),
                quantity=float(ld.get("quantity", 1)),
                unit_price=float(ld.get("unit_price", 0)),
                amount=amount,
                metadata=ld.get("metadata", {}),
            )
            lines.append(line)
            subtotal += amount

        now = datetime.now(timezone.utc)
        invoice = Invoice(
            invoice_id=self.store.new_id("inv"),
            invoice_number="",
            billing_account_id=account.billing_account_id,
            tenant_id=account.tenant_id,
            invoice_type=invoice_type,
            period_start=None,
            period_end=None,
            currency=account.currency,
            state="draft",
            lines=lines,
            subtotal=round(subtotal, 2),
            grand_total=round(subtotal, 2),
            subscription_id=body.get("subscription_id"),
            checkout_order_id=body.get("checkout_order_id"),
            created_at=now,
            updated_at=now,
        )
        for line in invoice.lines:
            line.invoice_id = invoice.invoice_id
        self.store.save_invoice(invoice)
        self._append_billing_record(invoice, "invoice_created", "system", "system", "")
        return 201, self._serialize_invoice(invoice)

    def validate_invoice(self, invoice_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        invoice, err = self._get_invoice(invoice_id, tenant_id)
        if err:
            return err
        if invoice.state != "draft":
            return 409, {"error": "invoice_must_be_in_draft_state"}
        invoice.state = "validated"
        invoice.version += 1
        invoice.updated_at = datetime.now(timezone.utc)
        self.store.save_invoice(invoice)
        self._append_billing_record(invoice, "invoice_validated", "system", "system", "")
        return 200, self._serialize_invoice(invoice)

    def issue_invoice(self, invoice_id: str, tenant_id: str, actor_id: str = "system") -> Tuple[int, Dict[str, Any]]:
        invoice, err = self._get_invoice(invoice_id, tenant_id)
        if err:
            return err
        if invoice.state != "validated":
            return 409, {"error": "invoice_must_be_validated_before_issuing"}

        before_state = invoice.state
        invoice.state = "issued"
        invoice.invoice_number = self.store.next_invoice_number()
        invoice.issued_at = datetime.now(timezone.utc)
        invoice.version += 1
        invoice.updated_at = invoice.issued_at
        self.store.save_invoice(invoice)
        self._append_billing_record(invoice, "invoice_issued", "user", actor_id, "")
        self._append_audit(invoice, "issue", {"state": before_state}, {"state": "issued"}, actor_id)
        return 200, self._serialize_invoice(invoice)

    def void_invoice(self, invoice_id: str, tenant_id: str, actor_id: str = "system") -> Tuple[int, Dict[str, Any]]:
        invoice, err = self._get_invoice(invoice_id, tenant_id)
        if err:
            return err
        if invoice.state not in ("issued", "overdue"):
            return 409, {"error": "only_issued_or_overdue_invoices_can_be_voided"}

        before_state = invoice.state
        invoice.state = "voided"
        invoice.voided_at = datetime.now(timezone.utc)
        invoice.version += 1
        invoice.updated_at = invoice.voided_at
        self.store.save_invoice(invoice)
        self._append_billing_record(invoice, "invoice_voided", "user", actor_id, "")
        self._append_audit(invoice, "void", {"state": before_state}, {"state": "voided"}, actor_id)
        return 200, self._serialize_invoice(invoice)

    def get_invoice(self, invoice_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        invoice, err = self._get_invoice(invoice_id, tenant_id)
        if err:
            return err
        return 200, self._serialize_invoice(invoice)

    def list_invoices(self, tenant_id: str, billing_account_id: Optional[str] = None) -> Tuple[int, Dict[str, Any]]:
        invoices = self.store.list_invoices(tenant_id, billing_account_id)
        return 200, {"invoices": [self._serialize_invoice(i) for i in invoices], "count": len(invoices)}

    def _get_invoice(self, invoice_id: str, tenant_id: str):
        invoice = self.store.get_invoice(invoice_id)
        if not invoice or invoice.tenant_id != tenant_id:
            return None, (404, {"error": "invoice_not_found"})
        return invoice, None

    def _append_billing_record(self, invoice: Invoice, record_type: str,
                                actor_type: str, actor_id: str, correlation_id: str) -> None:
        payload = json.dumps({"invoice_id": invoice.invoice_id, "state": invoice.state}, sort_keys=True)
        record = BillingRecord(
            record_id=self.store.new_id("br"),
            invoice_id=invoice.invoice_id,
            tenant_id=invoice.tenant_id,
            record_type=record_type,
            recorded_at=datetime.now(timezone.utc),
            actor_type=actor_type,
            actor_id=actor_id,
            correlation_id=correlation_id,
            payload_hash=hashlib.sha256(payload.encode()).hexdigest()[:16],
        )
        self.store.append_billing_record(record)

    def _append_audit(self, invoice: Invoice, action: str, before: dict, after: dict, actor: str) -> None:
        entry = AuditTrailEntry(
            audit_id=self.store.new_id("aud"),
            entity_type="invoice",
            entity_id=invoice.invoice_id,
            action=action,
            before=before,
            after=after,
            performed_by=actor,
            performed_at=datetime.now(timezone.utc),
        )
        self.store.append_audit(entry)

    def _serialize_account(self, a: BillingAccount) -> Dict[str, Any]:
        return {"billing_account_id": a.billing_account_id, "tenant_id": a.tenant_id,
                "customer_id": a.customer_id, "currency": a.currency, "status": a.status}

    def _serialize_invoice(self, i: Invoice) -> Dict[str, Any]:
        return {
            "invoice_id": i.invoice_id, "invoice_number": i.invoice_number,
            "billing_account_id": i.billing_account_id, "tenant_id": i.tenant_id,
            "invoice_type": i.invoice_type, "state": i.state, "currency": i.currency,
            "subtotal": i.subtotal, "grand_total": i.grand_total,
            "lines": [{"line_type": l.line_type, "quantity": l.quantity,
                        "unit_price": l.unit_price, "amount": l.amount} for l in i.lines],
            "version": i.version,
            "issued_at": i.issued_at.isoformat() if i.issued_at else None,
            "created_at": i.created_at.isoformat(),
        }
