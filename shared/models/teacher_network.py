from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal


@dataclass(frozen=True)
class TeacherTenantAffiliation:
    teacher_id: str
    home_tenant_id: str
    external_tenant_id: str
    linked_by_actor_id: str
    permission_scope: tuple[str, ...] = ()
    max_concurrent_batches: int = 1
    payout_tenant_id: str = ""
    payout_account_ref: str = ""
    is_active: bool = True
    linked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True)
class CrossInstitutionAssignment:
    teacher_id: str
    home_tenant_id: str
    target_tenant_id: str
    branch_id: str
    batch_id: str
    assigned_by_actor_id: str
    assignment_scope: str = "batch"
    payout_tenant_id: str = ""
    payout_rate: Decimal = Decimal("0")
    assigned_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
