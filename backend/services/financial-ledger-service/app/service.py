from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .models import FeeObligation, LedgerEntry, StudentBalance

ENTRY_TYPES = {"fee_charged", "payment_received", "credit_note", "refund", "adjustment"}
DEBIT_TYPES = {"fee_charged"}
CREDIT_TYPES = {"payment_received", "credit_note", "refund"}


class FinancialLedgerService:
    def __init__(self) -> None:
        self._entries: List[LedgerEntry] = []
        self._balances: Dict[str, StudentBalance] = {}
        self._obligations: Dict[str, FeeObligation] = {}

    def record_entry(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        entry_type = body.get("entry_type", "")
        if entry_type not in ENTRY_TYPES:
            return 400, {"error": "invalid_entry_type", "valid": list(ENTRY_TYPES)}

        student_id = body.get("student_id", "")
        tenant_id = body.get("tenant_id", "")
        amount = float(body.get("amount", 0))
        currency = body.get("currency", "USD")

        entry = LedgerEntry(
            entry_id=f"le-{secrets.token_urlsafe(8)}",
            student_id=student_id,
            tenant_id=tenant_id,
            entry_type=entry_type,
            amount=amount,
            currency=currency,
            reference=body.get("reference", ""),
            description=body.get("description", ""),
        )
        self._entries.append(entry)
        self._update_balance(student_id, tenant_id, currency, entry_type, amount)

        return 201, {
            "entry_id": entry.entry_id, "student_id": student_id,
            "entry_type": entry_type, "amount": amount, "currency": currency,
            "created_at": entry.created_at.isoformat(),
        }

    def get_balance(self, student_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        key = f"{tenant_id}:{student_id}"
        balance = self._balances.get(key)
        if not balance:
            return 200, {"student_id": student_id, "tenant_id": tenant_id,
                          "total_owed": 0.0, "total_paid": 0.0, "balance": 0.0, "overdue": False}
        return 200, {
            "student_id": balance.student_id, "tenant_id": balance.tenant_id,
            "currency": balance.currency, "total_owed": round(balance.total_owed, 2),
            "total_paid": round(balance.total_paid, 2), "balance": round(balance.balance, 2),
            "overdue": balance.overdue,
        }

    def add_obligation(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        obligation = FeeObligation(
            obligation_id=f"ob-{secrets.token_urlsafe(8)}",
            student_id=body.get("student_id", ""),
            tenant_id=body.get("tenant_id", ""),
            enrollment_id=body.get("enrollment_id", ""),
            amount=float(body.get("amount", 0)),
            currency=body.get("currency", "USD"),
            due_date=datetime.fromisoformat(body["due_date"]) if body.get("due_date") else datetime.now(timezone.utc),
        )
        self._obligations[obligation.obligation_id] = obligation
        # Record as fee_charged
        self.record_entry({
            "student_id": obligation.student_id, "tenant_id": obligation.tenant_id,
            "entry_type": "fee_charged", "amount": obligation.amount,
            "currency": obligation.currency, "reference": obligation.obligation_id,
            "description": f"Enrollment fee for {obligation.enrollment_id}",
        })
        return 201, {"obligation_id": obligation.obligation_id, "student_id": obligation.student_id,
                     "amount": obligation.amount, "status": obligation.status}

    def list_obligations(self, student_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        results = [o for o in self._obligations.values()
                   if o.student_id == student_id and o.tenant_id == tenant_id]
        now = datetime.now(timezone.utc)
        for ob in results:
            if ob.status == "pending" and ob.due_date.replace(tzinfo=timezone.utc) < now:
                ob.status = "overdue"
        return 200, {"obligations": [{"obligation_id": o.obligation_id, "enrollment_id": o.enrollment_id,
                                       "amount": o.amount, "status": o.status,
                                       "due_date": o.due_date.isoformat()} for o in results]}

    def list_entries(self, student_id: str, tenant_id: str) -> Tuple[int, Dict[str, Any]]:
        entries = [e for e in self._entries
                   if e.student_id == student_id and e.tenant_id == tenant_id]
        return 200, {"entries": [{"entry_id": e.entry_id, "entry_type": e.entry_type,
                                   "amount": e.amount, "reference": e.reference,
                                   "created_at": e.created_at.isoformat()} for e in entries]}

    def _update_balance(self, student_id: str, tenant_id: str, currency: str,
                        entry_type: str, amount: float) -> None:
        key = f"{tenant_id}:{student_id}"
        balance = self._balances.setdefault(
            key, StudentBalance(student_id=student_id, tenant_id=tenant_id, currency=currency)
        )
        if entry_type in DEBIT_TYPES:
            balance.total_owed += amount
            balance.balance += amount
        elif entry_type in CREDIT_TYPES:
            balance.total_paid += amount
            balance.balance -= amount
        balance.overdue = balance.balance > 0
        balance.last_updated = datetime.now(timezone.utc)
