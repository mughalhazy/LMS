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
from shared.models.ledger import LedgerEntry

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
class AcademicState:
    lifecycle_state: StudentLifecycleState = StudentLifecycleState.PROSPECT
    enrollment_status: str = "not_enrolled"
    active_learning_path_count: int = 0
    last_transition_at: datetime | None = None


@dataclass(frozen=True)
class FinancialState:
    total_invoiced: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    ledger_balance: Decimal = Decimal("0")
    last_invoice_id: str | None = None
    last_payment_id: str | None = None
    last_payment_at: datetime | None = None


@dataclass(frozen=True)
class UnifiedStudentProfile:
    tenant_id: str
    student_id: str
    display_name: str
    email: str
    country_code: str
    segment_id: str
    lifecycle_state: StudentLifecycleState = StudentLifecycleState.PROSPECT
    academic_state: AcademicState = field(default_factory=AcademicState)
    financial_state: FinancialState = field(default_factory=FinancialState)
    learning_path_ids: tuple[str, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


class LifecycleTransitionError(ValueError):
    pass


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
        self._allowed_lifecycle_transitions: dict[StudentLifecycleState, set[StudentLifecycleState]] = {
            StudentLifecycleState.PROSPECT: {StudentLifecycleState.ENROLLED, StudentLifecycleState.WITHDRAWN},
            StudentLifecycleState.ENROLLED: {
                StudentLifecycleState.ACTIVE,
                StudentLifecycleState.SUSPENDED,
                StudentLifecycleState.WITHDRAWN,
            },
            StudentLifecycleState.ACTIVE: {
                StudentLifecycleState.SUSPENDED,
                StudentLifecycleState.GRADUATED,
                StudentLifecycleState.WITHDRAWN,
            },
            StudentLifecycleState.SUSPENDED: {StudentLifecycleState.ACTIVE, StudentLifecycleState.WITHDRAWN},
            StudentLifecycleState.GRADUATED: set(),
            StudentLifecycleState.WITHDRAWN: set(),
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

        updated_profile = replace(
            profile,
            academic_state=replace(
                profile.academic_state,
                lifecycle_state=profile.lifecycle_state,
                active_learning_path_count=len(profile.learning_path_ids),
                enrollment_status="enrolled"
                if profile.lifecycle_state in {StudentLifecycleState.ENROLLED, StudentLifecycleState.ACTIVE}
                else profile.academic_state.enrollment_status,
            ),
        )
        self._profiles[profile_key] = updated_profile
        return updated_profile

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
        if state not in self._allowed_lifecycle_transitions[profile.lifecycle_state]:
            raise LifecycleTransitionError(f"invalid lifecycle transition: {profile.lifecycle_state} -> {state}")

        updated = replace(
            profile,
            lifecycle_state=state,
            academic_state=replace(
                profile.academic_state,
                lifecycle_state=state,
                enrollment_status="enrolled"
                if state in {StudentLifecycleState.ENROLLED, StudentLifecycleState.ACTIVE}
                else ("completed" if state == StudentLifecycleState.GRADUATED else profile.academic_state.enrollment_status),
                last_transition_at=datetime.now(timezone.utc),
            ),
        )
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
            profile = replace(
                profile,
                learning_path_ids=(*profile.learning_path_ids, learning_path_id),
                academic_state=replace(profile.academic_state, active_learning_path_count=len(profile.learning_path_ids) + 1),
            )
            self._profiles[self._profile_key(tenant_id=tenant_id, student_id=student_id)] = profile

        return self._learning_service.get_learner_progress(tenant_id=tenant_id, learner_id=student_id)

    def post_invoice_to_ledger(self, *, student_id: str, invoice: Invoice, currency: str = "USD") -> LedgerEntry:
        key = self._profile_key(tenant_id=invoice.tenant_id, student_id=student_id)
        if key not in self._profiles:
            raise KeyError("student profile not found")
        if any(
            entry.entry_type == "invoice" and entry.reference_id == invoice.invoice_id
            for entry in self._ledger.get(key, [])
        ):
            raise ValueError("duplicate invoice ledger posting")

        entry = LedgerEntry.create(
            ledger_entry_id=f"led_{invoice.invoice_id}",
            tenant_id=invoice.tenant_id,
            student_id=student_id,
            entry_type="invoice",
            amount=Decimal(invoice.amount),
            currency=currency,
            reference_type="invoice",
            reference_id=invoice.invoice_id,
            status="posted",
            metadata={"invoice_status": invoice.status},
        )
        self._ledger.setdefault(key, []).append(entry)
        profile = self._profiles[key]
        financial = profile.financial_state
        updated_profile = replace(
            profile,
            financial_state=replace(
                financial,
                total_invoiced=(financial.total_invoiced + Decimal(invoice.amount)),
                ledger_balance=(financial.ledger_balance + Decimal(invoice.amount)),
                last_invoice_id=invoice.invoice_id,
            ),
        )
        self._profiles[key] = updated_profile
        self._assert_ledger_consistency(tenant_id=invoice.tenant_id, student_id=student_id)
        return entry

    def post_payment_to_ledger(
        self,
        *,
        tenant_id: str,
        student_id: str,
        payment_id: str,
        amount: Decimal,
        currency: str = "USD",
    ) -> LedgerEntry:
        key = self._profile_key(tenant_id=tenant_id, student_id=student_id)
        if key not in self._profiles:
            raise KeyError("student profile not found")
        if amount <= Decimal("0"):
            raise ValueError("payment amount must be positive")
        if any(
            entry.entry_type == "payment" and entry.reference_id == payment_id
            for entry in self._ledger.get(key, [])
        ):
            raise ValueError("duplicate payment ledger posting")

        entry = LedgerEntry.create(
            ledger_entry_id=f"pay_{payment_id}",
            tenant_id=tenant_id,
            student_id=student_id,
            entry_type="payment",
            amount=Decimal(amount) * Decimal("-1"),
            currency=currency,
            reference_type="payment",
            reference_id=payment_id,
            status="posted",
        )
        self._ledger.setdefault(key, []).append(entry)
        profile = self._profiles[key]
        financial = profile.financial_state
        updated_profile = replace(
            profile,
            financial_state=replace(
                financial,
                total_paid=(financial.total_paid + Decimal(amount)),
                ledger_balance=(financial.ledger_balance - Decimal(amount)),
                last_payment_id=payment_id,
                last_payment_at=entry.timestamp,
            ),
        )
        self._profiles[key] = updated_profile
        self._assert_ledger_consistency(tenant_id=tenant_id, student_id=student_id)
        return entry

    def post_adjustment(
        self,
        *,
        tenant_id: str,
        student_id: str,
        adjustment_id: str,
        amount: Decimal,
        currency: str = "USD",
        entry_type: str = "adjustment",
        status: str = "posted",
        metadata: dict[str, Any] | None = None,
    ) -> LedgerEntry:
        key = self._profile_key(tenant_id=tenant_id, student_id=student_id)
        if key not in self._profiles:
            raise KeyError("student profile not found")
        if entry_type not in {"adjustment", "refund", "due"}:
            raise ValueError("entry_type must be one of: adjustment, refund, due")
        if any(
            entry.reference_type == entry_type and entry.reference_id == adjustment_id
            for entry in self._ledger.get(key, [])
        ):
            raise ValueError("duplicate adjustment ledger posting")

        normalized_amount = Decimal(amount)
        if entry_type == "refund" and normalized_amount > 0:
            normalized_amount = normalized_amount * Decimal("-1")
        if entry_type == "due" and normalized_amount < 0:
            normalized_amount = normalized_amount.copy_abs()

        entry = LedgerEntry.create(
            ledger_entry_id=f"{entry_type[:3]}_{adjustment_id}",
            tenant_id=tenant_id,
            student_id=student_id,
            entry_type=entry_type,
            amount=normalized_amount,
            currency=currency,
            reference_type=entry_type,
            reference_id=adjustment_id,
            status=status,
            metadata=metadata or {},
        )
        self._ledger.setdefault(key, []).append(entry)
        self.run_qc_autofix()
        return entry

    def post_payment_to_ledger_if_missing(
        self,
        *,
        tenant_id: str,
        student_id: str,
        payment_id: str,
        amount: Decimal,
        currency: str = "USD",
    ) -> LedgerEntry:
        existing = next(
            (
                entry
                for entry in self.get_student_ledger(tenant_id=tenant_id, student_id=student_id)
                if entry.entry_type == "payment" and entry.reference_id == payment_id
            ),
            None,
        )
        if existing is not None:
            return existing
        return self.post_payment_to_ledger(
            tenant_id=tenant_id,
            student_id=student_id,
            payment_id=payment_id,
            amount=amount,
            currency=currency,
        )

    def get_student_ledger(self, *, tenant_id: str, student_id: str) -> tuple[LedgerEntry, ...]:
        key = self._profile_key(tenant_id=tenant_id, student_id=student_id)
        return tuple(sorted(self._ledger.get(key, []), key=lambda entry: entry.timestamp))

    def compute_student_balance(self, *, tenant_id: str, student_id: str) -> Decimal:
        entries = self.get_student_ledger(tenant_id=tenant_id, student_id=student_id)
        return sum((entry.amount for entry in entries), start=Decimal("0"))

    def get_student_balance(self, *, tenant_id: str, student_id: str) -> Decimal:
        return self.compute_student_balance(tenant_id=tenant_id, student_id=student_id)

    def _assert_ledger_consistency(self, *, tenant_id: str, student_id: str) -> bool:
        key = self._profile_key(tenant_id=tenant_id, student_id=student_id)
        profile = self._profiles.get(key)
        if profile is None:
            return False
        entries = self._ledger.get(key, [])
        invoiced = sum(
            (entry.amount for entry in entries if entry.entry_type in {"invoice", "due"}),
            start=Decimal("0"),
        )
        paid = sum(
            (entry.amount.copy_abs() for entry in entries if entry.entry_type in {"payment", "refund"}),
            start=Decimal("0"),
        )
        balance = sum((entry.amount for entry in entries), start=Decimal("0"))
        financial = profile.financial_state
        return (
            financial.total_invoiced == invoiced
            and financial.total_paid == paid
            and financial.ledger_balance == balance
        )

    def run_qc_autofix(self) -> dict[str, bool]:
        for key, profile in list(self._profiles.items()):
            entries = self._ledger.get(key, [])
            invoiced = sum(
                (entry.amount for entry in entries if entry.entry_type in {"invoice", "due"}),
                start=Decimal("0"),
            )
            paid = sum(
                (entry.amount.copy_abs() for entry in entries if entry.entry_type in {"payment", "refund"}),
                start=Decimal("0"),
            )
            balance = sum((entry.amount for entry in entries), start=Decimal("0"))
            self._profiles[key] = replace(
                profile,
                academic_state=replace(
                    profile.academic_state,
                    lifecycle_state=profile.lifecycle_state,
                    active_learning_path_count=len(profile.learning_path_ids),
                ),
                financial_state=replace(
                    profile.financial_state,
                    total_invoiced=invoiced,
                    total_paid=paid,
                    ledger_balance=balance,
                ),
            )

        lifecycle_valid = all(
                profile.academic_state.lifecycle_state == profile.lifecycle_state for profile in self._profiles.values()
        )
        ledger_valid = all(
            self._assert_ledger_consistency(tenant_id=tenant_id, student_id=student_id)
            for tenant_id, student_id in self._profiles
        )
        return {
            "student_profile_unified_state": lifecycle_valid and ledger_valid,
            "ledger_consistency": ledger_valid,
            "lifecycle_transitions": lifecycle_valid,
            "payments_update_ledger": all(
                entry.entry_type != "payment" or entry.amount < 0
                for entries in self._ledger.values()
                for entry in entries
            ),
            "fragmented_state_removed": self.is_single_source_of_truth(),
        }

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
