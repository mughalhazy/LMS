from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


ONBOARDING_STEPS = [
    "tenant_record_created",
    "profile_detected",
    "config_bootstrapped",
    "capabilities_activated",
    "admin_provisioned",
    "guided_flow_started",
    "first_capability_activated",
]


@dataclass
class OnboardingSession:
    session_id: str
    tenant_id: str
    segment_type: str
    plan_type: str
    country_code: str
    steps: List[str]          # ordered step names
    completed_steps: List[str] = field(default_factory=list)
    current_step: int = 0
    status: str = "in_progress"  # in_progress | completed | failed
    wizard_data: Dict[str, Any] = field(default_factory=dict)
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class SmartDefault:
    area: str
    default_value: Any
    source: str
    customisable: bool = True
