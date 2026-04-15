from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
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

    # CGAP-043: BC-ECON-01 — map economic signals to a single priority suggested action.
    # Signal precedence (highest → lowest): unprofitable batches > low margin > outstanding dues > healthy.
    def _bc_econ01_suggested_action(
        self,
        *,
        gross_revenue: Decimal,
        estimated_costs: Decimal,
        outstanding_dues: Decimal,
        unprofitable_batch_count: int,
        profitability_by_branch: tuple[dict[str, Any], ...],
    ) -> str:
        if gross_revenue == Decimal("0"):
            return "No revenue recorded for this period — verify ledger entries and invoice sources."

        # Any unprofitable batches → review / consolidate.
        if unprofitable_batch_count > 0:
            return (
                f"{unprofitable_batch_count} batch(es) are operating at a loss. "
                "Review course pricing and learner count per batch, or consolidate low-enrollment batches."
            )

        # Margin < 15% → investigate cost drivers.
        if gross_revenue > Decimal("0"):
            margin = (gross_revenue - estimated_costs) / gross_revenue
            if margin < Decimal("0.15"):
                return (
                    "Profit margin is below 15%. "
                    "Review high-cost branches and consider re-pricing or reducing delivery overhead."
                )

        # Outstanding dues > 20% of gross revenue → collections action.
        if gross_revenue > Decimal("0") and outstanding_dues / gross_revenue > Decimal("0.20"):
            return (
                "Outstanding dues exceed 20% of gross revenue. "
                "Trigger payment reminders and review overdue learner accounts."
            )

        # Low-revenue branches alongside profitable ones → capability review.
        revenues = [Decimal(b.get("estimated_revenue", 0)) for b in profitability_by_branch]
        if revenues and max(revenues) > Decimal("0"):
            avg_rev = sum(revenues, Decimal("0")) / Decimal(len(revenues))
            low_branches = [b for b in profitability_by_branch if Decimal(b.get("estimated_revenue", 0)) < avg_rev * Decimal("0.5")]
            if low_branches:
                names = ", ".join(b.get("name", b.get("branch_id", "?")) for b in low_branches[:3])
                return (
                    f"Branch(es) {names} are generating less than half the average revenue. "
                    "Consider reviewing their course offerings or merging with higher-performing branches."
                )

        return "Economics are healthy. Monitor for trend changes next period."

    def list_unprofitable_batches(self, *, profitability_by_batch: Iterable[dict[str, Any]]) -> tuple[dict[str, Any], ...]:
        return tuple(item for item in profitability_by_batch if Decimal(item["estimated_profit"]) < 0)

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
    ) -> OwnerEconomicsSnapshot:
        ledger_entries = tuple(ledger_entries)
        commerce_invoices = tuple(commerce_invoices)
        batches = tuple(batches)
        branches = tuple(branches)

        revenue_per_student = self.compute_revenue_per_student(ledger_entries=ledger_entries, batches=batches)
        cashflow = self.compute_cashflow_summary(ledger_entries=ledger_entries)

        profitability_by_batch = []
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

        profitability_by_branch = self.list_branch_profitability(
            batches=batches,
            branches=branches,
            revenue_per_student=revenue_per_student,
        )

        estimated_costs = sum((Decimal(item["estimated_costs"]) for item in profitability_by_branch), start=Decimal("0"))
        invoice_gross = sum((Decimal(getattr(invoice, "amount", Decimal("0"))) for invoice in commerce_invoices), start=Decimal("0"))
        gross_revenue = max(cashflow["gross_revenue"], invoice_gross)

        composed_metadata = dict(metadata or {})
        composed_metadata["sources"] = {
            "ledger": len(ledger_entries),
            "commerce_invoices": len(commerce_invoices),
            "academy_batches": len(batches),
            "academy_branches": len(branches),
        }
        composed_metadata["unprofitable_batches"] = self.list_unprofitable_batches(
            profitability_by_batch=profitability_by_batch
        )

        # CGAP-043: BC-ECON-01 — compute priority suggested action from economic signals.
        suggested_action = self._bc_econ01_suggested_action(
            gross_revenue=gross_revenue,
            estimated_costs=estimated_costs,
            outstanding_dues=cashflow["outstanding_dues"],
            unprofitable_batch_count=len(composed_metadata["unprofitable_batches"]),
            profitability_by_branch=profitability_by_branch,
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
            metadata=composed_metadata,
            suggested_action=suggested_action,
        )
