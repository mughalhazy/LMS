from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

OnboardingMode = Literal["whatsapp_first", "dashboard"]
OnboardingStatus = Literal["created", "bootstrapping", "active", "completed", "failed"]


@dataclass(frozen=True)
class OnboardingSession:
    onboarding_id: str
    tenant_id: str
    onboarding_mode: OnboardingMode
    status: OnboardingStatus
    created_at: datetime
    completed_at: datetime | None = None
    initial_config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
