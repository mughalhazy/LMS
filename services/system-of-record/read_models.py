from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal

from shared.models.invoice import Invoice


@dataclass(frozen=True)
class AttendanceSummary:
    total_sessions: int
    attended_sessions: int
    attendance_rate: float
    last_attended_at: datetime | None
    status: str


@dataclass(frozen=True)
class ProgressSummary:
    active_learning_paths: int
    completed_learning_paths: int
    avg_progress_percent: float
    stalled_learning_paths: int
    status: str


@dataclass(frozen=True)
class FinancialStanding:
    total_invoiced: Decimal
    total_paid: Decimal
    ledger_balance: Decimal
    dues_amount: Decimal
    overdue_amount: Decimal
    standing: str


@dataclass(frozen=True)
class StudentOperationalState:
    tenant_id: str
    student_id: str
    display_name: str
    lifecycle_state: str
    batch_id: str | None
    class_status: str
    attendance: AttendanceSummary
    progress: ProgressSummary
    financial: FinancialStanding
    has_dues: bool
    is_overdue: bool
    is_inactive: bool
    at_risk: bool
    at_risk_reasons: tuple[str, ...]


def build_financial_standing(
    *,
    profile: object,
    invoices: tuple[Invoice, ...],
) -> FinancialStanding:
    overdue_amount = sum(
        (Decimal(invoice.amount) for invoice in invoices if invoice.status == "overdue"),
        start=Decimal("0"),
    )
    financial_state = getattr(profile, "financial_state")
    dues_amount = max(financial_state.ledger_balance, Decimal("0"))
    if overdue_amount > 0:
        standing = "overdue"
    elif dues_amount > 0:
        standing = "due"
    else:
        standing = "clear"
    return FinancialStanding(
        total_invoiced=financial_state.total_invoiced,
        total_paid=financial_state.total_paid,
        ledger_balance=financial_state.ledger_balance,
        dues_amount=dues_amount,
        overdue_amount=overdue_amount,
        standing=standing,
    )


def is_profile_inactive(
    *,
    profile: object,
    today: date,
    inactivity_days: int,
    paused_lifecycle_states: tuple[str, ...] = ("paused", "dropped"),
) -> bool:
    lifecycle_state = str(getattr(profile, "lifecycle_state", "")).lower()
    if lifecycle_state in paused_lifecycle_states:
        return True

    metadata = getattr(profile, "metadata", {}) or {}
    last_active_raw = str(metadata.get("activity.last_active_at", "")).strip()
    if not last_active_raw:
        return False
    try:
        last_active = datetime.fromisoformat(last_active_raw.replace("Z", "+00:00")).astimezone(timezone.utc).date()
    except ValueError:
        return False
    return (today - last_active).days >= max(0, int(inactivity_days))
