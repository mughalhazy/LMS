from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AcademyDeliveryMode(str, Enum):
    SELF_PACED = "self_paced"
    COHORT_BASED = "cohort_based"


class AcademyPackage(str, Enum):
    FOUNDATION = "foundation"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class AcademyEnrollment:
    tenant_id: str
    academy_id: str
    cohort_id: str
    learner_id: str
    package: AcademyPackage

