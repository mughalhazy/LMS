from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class BranchStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


@dataclass(frozen=True)
class Branch:
    branch_id: str
    tenant_id: str
    name: str
    code: str
    location: str
    manager_id: str | None = None
    capacity: int = 0
    active_batches: tuple[str, ...] = ()
    status: BranchStatus = BranchStatus.ACTIVE
    metadata: dict[str, str] = field(default_factory=dict)
