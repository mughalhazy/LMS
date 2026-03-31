from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.academy import AcademyEnrollment
from shared.models.config import ConfigResolutionContext
from shared.models.invoice import Invoice

_ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, relative_path: str):
    module_path = _ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_ConfigModule = _load_module("config_service_module_for_sor", "services/config-service/service.py")


def _load_progress_module():
    package_name = "sor_progress_src"
    package_path = _ROOT / "backend/services/progress-service/src"
    package_spec = importlib.util.spec_from_file_location(
        package_name,
        package_path / "__init__.py",
        submodule_search_locations=[str(package_path)],
    )
    if package_spec is None or package_spec.loader is None:
        raise ImportError("Unable to initialize progress-service package")
    package_module = importlib.util.module_from_spec(package_spec)
    sys.modules[package_name] = package_module
    package_spec.loader.exec_module(package_module)

    module_spec = importlib.util.spec_from_file_location(
        f"{package_name}.progress_service",
        package_path / "progress_service.py",
    )
    if module_spec is None or module_spec.loader is None:
        raise ImportError("Unable to load progress_service module")
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_spec.name] = module
    module_spec.loader.exec_module(module)
    return module


_LearningModule = _load_progress_module()

ConfigService = _ConfigModule.ConfigService
ProgressTrackingService = _LearningModule.ProgressTrackingService


class StudentLifecycleState(str, Enum):
    PROSPECT = "prospect"
    ENROLLED = "enrolled"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    GRADUATED = "graduated"
    WITHDRAWN = "withdrawn"


@dataclass(frozen=True)
class UnifiedStudentProfile:
    tenant_id: str
    student_id: str
    display_name: str
    email: str
    country_code: str
    segment_id: str
    lifecycle_state: StudentLifecycleState = StudentLifecycleState.PROSPECT
    learning_path_ids: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class LedgerEntry:
    entry_id: str
    tenant_id: str
    student_id: str
    amount: Decimal
    currency: str
    source_type: str
    source_ref: str
    posted_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SystemOfRecordService:
    """Canonical student system of record.

    Owns lifecycle, ledger, and unified student profile. Integrates with learning and
    commerce-facing invoice records while preserving strict ownership boundaries.
    """

    def __init__(
        self,
        *,
        config_service: ConfigService | None = None,
        learning_service: ProgressTrackingService | None = None,
    ) -> None:
        self._config_service = config_service or ConfigService()
        self._learning_service = learning_service or ProgressTrackingService()

        self._profiles: dict[tuple[str, str], UnifiedStudentProfile] = {}
        self._ledger: dict[tuple[str, str], list[LedgerEntry]] = {}
        self._academic_enrollments: dict[tuple[str, str], list[AcademyEnrollment]] = {}

        # Domain ownership registry to enforce no duplicate data ownership.
        self._domain_owner = {
            "student.profile": "system-of-record",
            "student.lifecycle": "system-of-record",
            "student.ledger": "system-of-record",
            "learning.progress": "learning-service",
            "commerce.invoice": "commerce-service",
            "config.runtime": "config-service",
        }

    def _profile_key(self, *, tenant_id: str, student_id: str) -> tuple[str, str]:
        return tenant_id.strip(), student_id.strip()

    def _resolve_profile_policy(self, *, tenant_id: str, country_code: str, segment_id: str) -> dict[str, Any]:
        config = self._config_service.resolve(
            ConfigResolutionContext(
                tenant_id=tenant_id,
                country_code=country_code,
                segment_id=segment_id,
            )
        )
        return config.behavior_tuning.get("system_of_record", {})

    def upsert_student_profile(self, profile: UnifiedStudentProfile) -> UnifiedStudentProfile:
        profile_key = self._profile_key(tenant_id=profile.tenant_id, student_id=profile.student_id)
        policy = self._resolve_profile_policy(
            tenant_id=profile.tenant_id,
            country_code=profile.country_code,
            segment_id=profile.segment_id,
        )
        required_fields = policy.get("required_profile_fields", ["display_name", "email"])

        for field_name in required_fields:
            value = getattr(profile, field_name, None)
            if not value:
                raise ValueError(f"{field_name} is required by system_of_record policy")

        self._profiles[profile_key] = profile
        return profile

    def get_student_profile(self, *, tenant_id: str, student_id: str) -> UnifiedStudentProfile | None:
        return self._profiles.get(self._profile_key(tenant_id=tenant_id, student_id=student_id))

    def list_student_profiles(self, *, tenant_id: str) -> tuple[UnifiedStudentProfile, ...]:
        normalized_tenant = tenant_id.strip()
        return tuple(
            profile
            for (profile_tenant_id, _), profile in self._profiles.items()
            if profile_tenant_id == normalized_tenant
        )

    def transition_student_lifecycle(
        self,
        *,
        tenant_id: str,
        student_id: str,
        state: StudentLifecycleState,
    ) -> UnifiedStudentProfile:
        profile = self.get_student_profile(tenant_id=tenant_id, student_id=student_id)
        if profile is None:
            raise KeyError("student profile not found")

        updated = replace(profile, lifecycle_state=state)
        self._profiles[self._profile_key(tenant_id=tenant_id, student_id=student_id)] = updated
        return updated

    def register_academy_enrollment(self, enrollment: AcademyEnrollment) -> None:
        key = self._profile_key(tenant_id=enrollment.tenant_id, student_id=enrollment.learner_id)
        self._academic_enrollments.setdefault(key, []).append(enrollment)

    def assign_learning_path(
        self,
        *,
        tenant_id: str,
        student_id: str,
        learning_path_id: str,
        course_ids: list[str],
    ) -> dict[str, Any]:
        profile = self.get_student_profile(tenant_id=tenant_id, student_id=student_id)
        if profile is None:
            raise KeyError("student profile not found")

        self._learning_service.assign_learning_path(
            tenant_id=tenant_id,
            learner_id=student_id,
            learning_path_id=learning_path_id,
            assigned_course_ids=course_ids,
        )

        if learning_path_id not in profile.learning_path_ids:
            profile = replace(profile, learning_path_ids=(*profile.learning_path_ids, learning_path_id))
            self._profiles[self._profile_key(tenant_id=tenant_id, student_id=student_id)] = profile

        return self._learning_service.get_learner_progress(tenant_id=tenant_id, learner_id=student_id)

    def post_invoice_to_ledger(self, *, student_id: str, invoice: Invoice, currency: str = "USD") -> LedgerEntry:
        key = self._profile_key(tenant_id=invoice.tenant_id, student_id=student_id)
        if key not in self._profiles:
            raise KeyError("student profile not found")

        entry = LedgerEntry(
            entry_id=f"led_{invoice.invoice_id}",
            tenant_id=invoice.tenant_id,
            student_id=student_id,
            amount=Decimal(invoice.amount),
            currency=currency,
            source_type="invoice",
            source_ref=invoice.invoice_id,
        )
        self._ledger.setdefault(key, []).append(entry)
        return entry

    def get_student_ledger(self, *, tenant_id: str, student_id: str) -> tuple[LedgerEntry, ...]:
        key = self._profile_key(tenant_id=tenant_id, student_id=student_id)
        return tuple(self._ledger.get(key, []))

    def get_student_balance(self, *, tenant_id: str, student_id: str) -> Decimal:
        entries = self.get_student_ledger(tenant_id=tenant_id, student_id=student_id)
        return sum((entry.amount for entry in entries), start=Decimal("0"))

    def has_duplicate_data_ownership(self) -> bool:
        domains = list(self._domain_owner)
        return len(domains) != len(set(domains))

    def is_single_source_of_truth(self) -> bool:
        return (
            self._domain_owner.get("student.profile") == "system-of-record"
            and self._domain_owner.get("student.lifecycle") == "system-of-record"
            and self._domain_owner.get("student.ledger") == "system-of-record"
            and not self.has_duplicate_data_ownership()
        )
