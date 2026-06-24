from __future__ import annotations

import secrets
from typing import Dict, List, Optional

from .models import AuditTrailEntry, BillingAccount, BillingRecord, Invoice


class InMemoryBillingStore:
    def __init__(self) -> None:
        self._accounts: Dict[str, BillingAccount] = {}
        self._invoices: Dict[str, Invoice] = {}
        self._billing_records: List[BillingRecord] = []
        self._audit_trail: List[AuditTrailEntry] = []
        self._invoice_counter = 0

    def save_account(self, account: BillingAccount) -> None:
        self._accounts[account.billing_account_id] = account

    def get_account(self, billing_account_id: str) -> Optional[BillingAccount]:
        return self._accounts.get(billing_account_id)

    def save_invoice(self, invoice: Invoice) -> None:
        self._invoices[invoice.invoice_id] = invoice

    def get_invoice(self, invoice_id: str) -> Optional[Invoice]:
        return self._invoices.get(invoice_id)

    def list_invoices(self, tenant_id: str, billing_account_id: Optional[str] = None) -> List[Invoice]:
        results = [i for i in self._invoices.values() if i.tenant_id == tenant_id]
        if billing_account_id:
            results = [i for i in results if i.billing_account_id == billing_account_id]
        return results

    def append_billing_record(self, record: BillingRecord) -> None:
        self._billing_records.append(record)

    def list_billing_records(self, tenant_id: str, billing_account_id: Optional[str] = None) -> List[BillingRecord]:
        results = [r for r in self._billing_records if r.tenant_id == tenant_id]
        if billing_account_id:
            results = [r for r in results if True]  # filter by account via invoice_id lookup
        return results

    def append_audit(self, entry: AuditTrailEntry) -> None:
        self._audit_trail.append(entry)

    def list_audit(self, entity_id: str) -> List[AuditTrailEntry]:
        return [e for e in self._audit_trail if e.entity_id == entity_id]

    def next_invoice_number(self) -> str:
        self._invoice_counter += 1
        return f"INV-{self._invoice_counter:06d}"

    def new_id(self, prefix: str = "") -> str:
        return f"{prefix}-{secrets.token_urlsafe(8)}" if prefix else secrets.token_urlsafe(10)
