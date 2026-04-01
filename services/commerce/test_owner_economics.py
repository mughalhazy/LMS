from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from services.commerce.owner_economics import OwnerEconomicsEngine


def test_owner_economics_snapshot_and_lists() -> None:
    engine = OwnerEconomicsEngine()
    ledger_entries = (
        SimpleNamespace(student_id="s1", source_type="invoice", amount=Decimal("100")),
        SimpleNamespace(student_id="s1", source_type="payment", amount=Decimal("-60")),
        SimpleNamespace(student_id="s2", source_type="invoice", amount=Decimal("80")),
    )
    batches = (
        SimpleNamespace(batch_id="b1", branch_id="br1", learner_ids=("s1",), metadata={"estimated_cost": "70"}),
        SimpleNamespace(batch_id="b2", branch_id="br1", learner_ids=("s2",), metadata={"estimated_cost": "120"}),
    )
    branches = (SimpleNamespace(branch_id="br1", name="Downtown", active_batches=("b1", "b2"), metadata={"estimated_overhead": "10"}),)
    invoices = (SimpleNamespace(amount=Decimal("180")),)

    revenue_per_student = engine.compute_revenue_per_student(ledger_entries=ledger_entries, batches=batches)
    assert revenue_per_student == Decimal("90.00")

    summary = engine.compute_cashflow_summary(ledger_entries=ledger_entries)
    assert summary["total_cash_in"] == Decimal("60")
    assert summary["outstanding_dues"] == Decimal("120")

    snapshot = engine.compute_profitability_snapshot(
        tenant_id="tenant_x",
        reporting_period="2026-03",
        ledger_entries=ledger_entries,
        commerce_invoices=invoices,
        batches=batches,
        branches=branches,
        operations_actions=(
            SimpleNamespace(
                action_id="action:tenant_x:1",
                action_type="unpaid_fees_follow_up",
                priority="high",
                reason="Outstanding unpaid fee case",
            ),
        ),
    )
    assert snapshot.revenue_per_student == Decimal("90.00")
    assert snapshot.gross_revenue == Decimal("180")
    assert len(snapshot.profitability_by_batch) == 2
    assert len(engine.list_unprofitable_batches(profitability_by_batch=snapshot.profitability_by_batch)) == 1
    assert snapshot.metadata["sources"]["ledger"] == 3
    assert len(snapshot.revenue_per_batch) == 2
    assert len(snapshot.cashflow_timeline) >= 1
    assert snapshot.profitability["is_profitable"] is False
    assert {trigger["trigger_type"] for trigger in snapshot.action_triggers} >= {
        "dues_collection",
        "batch_profitability_intervention",
        "operations_os_action",
    }
