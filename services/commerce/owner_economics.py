from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable

from shared.models.owner_economics import OwnerEconomicsSnapshot


@dataclass
class OwnerEconomicsEngine:
    """Canonical owner economics engine derived from ledger + commerce + academy ops."""

    def _invoice_amount(self, entry: Any) -> Decimal:
        source_type = str(getattr(entry, "source_type", "")).lower()
        if source_type == "invoice":
            return Decimal(getattr(entry, "amount", Decimal("0")))
        return Decimal("0")

    def _payment_amount(self, entry: Any) -> Decimal:
        source_type = str(getattr(entry, "source_type", "")).lower()
        if source_type == "payment":
            return Decimal(getattr(entry, "amount", Decimal("0"))).copy_abs()
        return Decimal("0")

    def _estimate_batch_cost(self, batch: Any) -> Decimal:
        metadata = dict(getattr(batch, "metadata", {}) or {})
        if "estimated_cost" in metadata:
            return Decimal(str(metadata["estimated_cost"]))
        learner_count = len(getattr(batch, "learner_ids", ()) or ())
        return Decimal(learner_count) * Decimal("15")

    def _estimate_branch_overhead(self, branch: Any) -> Decimal:
        metadata = dict(getattr(branch, "metadata", {}) or {})
        if "estimated_overhead" in metadata:
            return Decimal(str(metadata["estimated_overhead"]))
        active_batches = len(getattr(branch, "active_batches", ()) or ())
        return Decimal(active_batches) * Decimal("25")

    def _entry_date(self, entry: Any) -> str:
        for field_name in ("occurred_at", "created_at", "entry_date", "timestamp"):
            value = getattr(entry, field_name, None)
            if value is None:
                continue
            if isinstance(value, datetime):
                return value.date().isoformat()
            if isinstance(value, date):
                return value.isoformat()
            value_str = str(value).strip()
            if value_str:
                return value_str.split("T")[0]
        return "undated"

    def compute_revenue_per_student(self, *, ledger_entries: Iterable[Any], batches: Iterable[Any]) -> Decimal:
        ledger_entries = tuple(ledger_entries)
        unique_students = {
            getattr(entry, "student_id", "")
            for entry in ledger_entries
            if getattr(entry, "student_id", "")
        }
        if not unique_students:
            unique_students = {
                learner_id
                for batch in batches
                for learner_id in (getattr(batch, "learner_ids", ()) or ())
                if learner_id
            }
        student_count = len(unique_students)
        if student_count == 0:
            return Decimal("0")
        gross_revenue = sum((self._invoice_amount(entry) for entry in ledger_entries), start=Decimal("0"))
        return (gross_revenue / Decimal(student_count)).quantize(Decimal("0.01"))

    def compute_cashflow_summary(self, *, ledger_entries: Iterable[Any]) -> dict[str, Decimal]:
        ledger_entries = tuple(ledger_entries)
        total_cash_in = sum((self._payment_amount(entry) for entry in ledger_entries), start=Decimal("0"))

        by_student: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
        for entry in ledger_entries:
            student_id = getattr(entry, "student_id", "")
            if student_id:
                by_student[student_id] += Decimal(getattr(entry, "amount", Decimal("0")))
        outstanding_dues = sum((max(balance, Decimal("0")) for balance in by_student.values()), start=Decimal("0"))

        gross_revenue = sum((self._invoice_amount(entry) for entry in ledger_entries), start=Decimal("0"))
        return {
            "total_cash_in": total_cash_in,
            "outstanding_dues": outstanding_dues,
            "gross_revenue": gross_revenue,
        }

    def compute_cashflow_timeline(self, *, ledger_entries: Iterable[Any]) -> tuple[dict[str, Any], ...]:
        daily: dict[str, dict[str, Decimal]] = {}
        for entry in ledger_entries:
            day = self._entry_date(entry)
            bucket = daily.setdefault(
                day,
                {"cash_in": Decimal("0"), "invoiced": Decimal("0"), "net_cashflow": Decimal("0")},
            )
            payment = self._payment_amount(entry)
            invoiced = self._invoice_amount(entry)
            bucket["cash_in"] += payment
            bucket["invoiced"] += invoiced
            bucket["net_cashflow"] += payment - invoiced

        return tuple(
            {
                "date": day,
                "cash_in": values["cash_in"],
                "invoiced": values["invoiced"],
                "net_cashflow": values["net_cashflow"],
            }
            for day, values in sorted(daily.items(), key=lambda item: item[0])
        )

    def list_branch_profitability(self, *, batches: Iterable[Any], branches: Iterable[Any], revenue_per_student: Decimal) -> tuple[dict[str, Any], ...]:
        branch_profit: dict[str, dict[str, Any]] = {}
        for branch in branches:
            branch_id = getattr(branch, "branch_id", "")
            branch_profit[branch_id] = {
                "branch_id": branch_id,
                "name": getattr(branch, "name", branch_id),
                "estimated_revenue": Decimal("0"),
                "estimated_costs": self._estimate_branch_overhead(branch),
                "estimated_profit": Decimal("0"),
            }

        for batch in batches:
            branch_id = getattr(batch, "branch_id", "")
            if branch_id not in branch_profit:
                branch_profit[branch_id] = {
                    "branch_id": branch_id,
                    "name": branch_id,
                    "estimated_revenue": Decimal("0"),
                    "estimated_costs": Decimal("0"),
                    "estimated_profit": Decimal("0"),
                }
            batch_learners = len(getattr(batch, "learner_ids", ()) or ())
            estimated_revenue = Decimal(batch_learners) * revenue_per_student
            estimated_cost = self._estimate_batch_cost(batch)
            branch_profit[branch_id]["estimated_revenue"] += estimated_revenue
            branch_profit[branch_id]["estimated_costs"] += estimated_cost

        for payload in branch_profit.values():
            payload["estimated_profit"] = payload["estimated_revenue"] - payload["estimated_costs"]

        return tuple(sorted(branch_profit.values(), key=lambda item: item["branch_id"]))

    def list_unprofitable_batches(self, *, profitability_by_batch: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
        return tuple(item for item in profitability_by_batch if Decimal(item["estimated_profit"]) < 0)

    def _derive_action_triggers(
        self,
        *,
        cashflow: dict[str, Decimal],
        profitability_by_batch: Iterable[dict[str, Any]],
        operations_actions: Iterable[Any] = (),
    ) -> tuple[dict[str, Any], ...]:
        triggers: list[dict[str, Any]] = []
        if cashflow["outstanding_dues"] > 0:
            triggers.append(
                {
                    "trigger_type": "dues_collection",
                    "severity": "high",
                    "reason": f"Outstanding dues detected: {cashflow['outstanding_dues']}",
                    "suggested_action": "Run payment follow-up sequence for overdue learners.",
                }
            )

        for row in profitability_by_batch:
            if Decimal(row["estimated_profit"]) < 0:
                triggers.append(
                    {
                        "trigger_type": "batch_profitability_intervention",
                        "severity": "high",
                        "batch_id": row["batch_id"],
                        "reason": f"Batch {row['batch_id']} is loss-making.",
                        "suggested_action": "Review pricing, cost structure, and occupancy for this batch.",
                    }
                )

        for action in operations_actions:
            action_id = str(getattr(action, "action_id", ""))
            action_type = str(getattr(action, "action_type", "operations_action"))
            reason = str(getattr(action, "reason", "")).strip() or "Operations action pending."
            triggers.append(
                {
                    "trigger_type": "operations_os_action",
                    "severity": str(getattr(action, "priority", "medium")),
                    "action_id": action_id,
                    "reason": reason,
                    "suggested_action": f"Execute operations-os action: {action_type}.",
                }
            )

        deduped: dict[str, dict[str, Any]] = {}
        for trigger in triggers:
            key = f"{trigger.get('trigger_type')}:{trigger.get('batch_id', '')}:{trigger.get('action_id', '')}:{trigger.get('reason')}"
            deduped.setdefault(key, trigger)
        return tuple(deduped.values())

    def compute_profitability_snapshot(
        self,
        *,
        tenant_id: str,
        reporting_period: str,
        ledger_entries: Iterable[Any],
        commerce_invoices: Iterable[Any],
        batches: Iterable[Any],
        branches: Iterable[Any],
        metadata: dict[str, Any] | None = None,
        operations_actions: Iterable[Any] = (),
    ) -> OwnerEconomicsSnapshot:
        ledger_entries = tuple(ledger_entries)
        commerce_invoices = tuple(commerce_invoices)
        batches = tuple(batches)
        branches = tuple(branches)
        operations_actions = tuple(operations_actions)

        revenue_per_student = self.compute_revenue_per_student(ledger_entries=ledger_entries, batches=batches)
        cashflow = self.compute_cashflow_summary(ledger_entries=ledger_entries)
        cashflow_timeline = self.compute_cashflow_timeline(ledger_entries=ledger_entries)

        profitability_by_batch: list[dict[str, Any]] = []
        for batch in batches:
            student_count = len(getattr(batch, "learner_ids", ()) or ())
            estimated_revenue = Decimal(student_count) * revenue_per_student
            estimated_cost = self._estimate_batch_cost(batch)
            profitability_by_batch.append(
                {
                    "batch_id": getattr(batch, "batch_id", ""),
                    "branch_id": getattr(batch, "branch_id", ""),
                    "learner_count": student_count,
                    "estimated_revenue": estimated_revenue,
                    "estimated_costs": estimated_cost,
                    "estimated_profit": estimated_revenue - estimated_cost,
                }
            )
        revenue_per_batch = tuple(
            {
                "batch_id": row["batch_id"],
                "branch_id": row["branch_id"],
                "learner_count": row["learner_count"],
                "estimated_revenue": row["estimated_revenue"],
            }
            for row in profitability_by_batch
        )

        profitability_by_branch = self.list_branch_profitability(
            batches=batches,
            branches=branches,
            revenue_per_student=revenue_per_student,
        )

        estimated_costs = sum((Decimal(item["estimated_costs"]) for item in profitability_by_branch), start=Decimal("0"))
        invoice_gross = sum((Decimal(getattr(invoice, "amount", Decimal("0"))) for invoice in commerce_invoices), start=Decimal("0"))
        gross_revenue = max(cashflow["gross_revenue"], invoice_gross)
        profitability = {
            "gross_margin": ((gross_revenue - estimated_costs) / gross_revenue).quantize(Decimal("0.0001"))
            if gross_revenue > 0
            else Decimal("0"),
            "is_profitable": (gross_revenue - estimated_costs) >= 0,
            "unprofitable_batch_count": len(self.list_unprofitable_batches(profitability_by_batch=profitability_by_batch)),
        }
        action_triggers = self._derive_action_triggers(
            cashflow=cashflow,
            profitability_by_batch=profitability_by_batch,
            operations_actions=operations_actions,
        )

        composed_metadata = dict(metadata or {})
        composed_metadata["sources"] = {
            "ledger": len(ledger_entries),
            "commerce_invoices": len(commerce_invoices),
            "academy_batches": len(batches),
            "academy_branches": len(branches),
            "operations_actions": len(operations_actions),
        }
        composed_metadata["unprofitable_batches"] = self.list_unprofitable_batches(
            profitability_by_batch=profitability_by_batch
        )

        return OwnerEconomicsSnapshot(
            tenant_id=tenant_id,
            reporting_period=reporting_period,
            revenue_per_student=revenue_per_student,
            total_cash_in=cashflow["total_cash_in"],
            outstanding_dues=cashflow["outstanding_dues"],
            gross_revenue=gross_revenue,
            estimated_costs=estimated_costs,
            estimated_profit=gross_revenue - estimated_costs,
            profitability_by_batch=tuple(profitability_by_batch),
            profitability_by_branch=profitability_by_branch,
            revenue_per_batch=revenue_per_batch,
            cashflow_timeline=cashflow_timeline,
            profitability=profitability,
            action_triggers=action_triggers,
            metadata=composed_metadata,
        )
