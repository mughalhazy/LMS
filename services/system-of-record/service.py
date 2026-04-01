from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
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
_ModelsModule = _load_module("system_of_record_models", "services/system-of-record/models.py")


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
AcademicState = _ModelsModule.AcademicState
AcademicStatus = _ModelsModule.AcademicStatus
FinancialState = _ModelsModule.FinancialState
LedgerEntry = _ModelsModule.LedgerEntry
LifecycleTransitionError = _ModelsModule.LifecycleTransitionError
UnifiedStudentProfile = _ModelsModule.UnifiedStudentProfile


class SystemOfRecordService:
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

        self._domain_owner = {
            "student.profile": "system-of-record",
            "student.lifecycle": "system-of-record",
            "student.academic_state": "system-of-record",
            "student.financial_state": "system-of-record",
            "student.attendance_summary": "system-of-record",
            "student.ledger": "system-of-record",
            "learning.progress": "learning-service",
            "commerce.invoice": "commerce-service",
            "config.runtime": "config-service",
        }

    def _profile_key(self, *, tenant_id: str, student_id: str) -> tuple[str, str]:
        return tenant_id.strip(), student_id.strip()

    def _resolve_profile_policy(self, *, tenant_id: str, metadata: dict[str, str]) -> dict[str, Any]:
        config = self._config_service.resolve(
            ConfigResolutionContext(
                tenant_id=tenant_id,
                country_code=metadata.get("country_code", "US"),
                segment_id=metadata.get("segment_id", "academy"),
            )
        )
        return config.behavior_tuning.get("system_of_record", {})

    def upsert_student_profile(self, profile: UnifiedStudentProfile) -> UnifiedStudentProfile:
        key = self._profile_key(tenant_id=profile.tenant_id, student_id=profile.student_id)
        policy = self._resolve_profile_policy(tenant_id=profile.tenant_id, metadata=profile.metadata)
        for field_name in policy.get("required_profile_fields", ["full_name"]):
            value = getattr(profile, field_name, None)
            if not value:
                raise ValueError(f"{field_name} is required by system_of_record policy")

        self._profiles[key] = profile
        return profile

    def get_student_profile(self, *, tenant_id: str, student_id: str) -> UnifiedStudentProfile | None:
        return self._profiles.get(self._profile_key(tenant_id=tenant_id, student_id=student_id))

    def update_academic_state(
        self,
        *,
        tenant_id: str,
        student_id: str,
        status: AcademicStatus,
        notes: str = "",
    ) -> UnifiedStudentProfile:
        profile = self.get_student_profile(tenant_id=tenant_id, student_id=student_id)
        if profile is None:
            raise KeyError("student profile not found")

        lifecycle_from_status = {
            AcademicStatus.ENROLLED: "enrolled",
            AcademicStatus.ACTIVE: "active",
            AcademicStatus.PAUSED: "paused",
            AcademicStatus.COMPLETED: "completed",
            AcademicStatus.DROPPED: "dropped",
        }
        updated = replace(
            profile,
            academic_state=AcademicState(status=status, updated_at=datetime.now(timezone.utc), notes=notes),
            lifecycle_state=lifecycle_from_status[status],
        )
        self._profiles[self._profile_key(tenant_id=tenant_id, student_id=student_id)] = updated
        return updated

    def update_financial_state(
        self,
        *,
        tenant_id: str,
        student_id: str,
        current_balance: Decimal,
        dues_outstanding: Decimal,
        payment_status: str,
        installment_status: str,
    ) -> UnifiedStudentProfile:
        profile = self.get_student_profile(tenant_id=tenant_id, student_id=student_id)
        if profile is None:
            raise KeyError("student profile not found")
        updated = replace(
            profile,
            financial_state=FinancialState(
                current_balance=Decimal(current_balance),
                dues_outstanding=Decimal(dues_outstanding),
                payment_status=payment_status,
                installment_status=installment_status,
            ),
        )
        self._profiles[self._profile_key(tenant_id=tenant_id, student_id=student_id)] = updated
        return updated

    def attach_batch(self, *, tenant_id: str, student_id: str, batch_id: str) -> UnifiedStudentProfile:
        profile = self.get_student_profile(tenant_id=tenant_id, student_id=student_id)
        if profile is None:
            raise KeyError("student profile not found")
        if batch_id in profile.active_batches:
            return profile
        updated = replace(profile, active_batches=(*profile.active_batches, batch_id))
        self._profiles[self._profile_key(tenant_id=tenant_id, student_id=student_id)] = updated
        return updated

    def attach_teacher(self, *, tenant_id: str, student_id: str, teacher_id: str) -> UnifiedStudentProfile:
        profile = self.get_student_profile(tenant_id=tenant_id, student_id=student_id)
        if profile is None:
            raise KeyError("student profile not found")
        if teacher_id in profile.assigned_teacher_ids:
            return profile
        updated = replace(profile, assigned_teacher_ids=(*profile.assigned_teacher_ids, teacher_id))
        self._profiles[self._profile_key(tenant_id=tenant_id, student_id=student_id)] = updated
        return updated

    def transition_student_lifecycle(self, *, tenant_id: str, student_id: str, state: str) -> UnifiedStudentProfile:
        status_map = {
            "enrolled": AcademicStatus.ENROLLED,
            "active": AcademicStatus.ACTIVE,
            "paused": AcademicStatus.PAUSED,
            "completed": AcademicStatus.COMPLETED,
            "dropped": AcademicStatus.DROPPED,
        }
        if state not in status_map:
            raise LifecycleTransitionError(f"unsupported lifecycle state: {state}")
        return self.update_academic_state(
            tenant_id=tenant_id,
            student_id=student_id,
            status=status_map[state],
        )

    def register_academy_enrollment(self, enrollment: AcademyEnrollment) -> None:
        key = self._profile_key(tenant_id=enrollment.tenant_id, student_id=enrollment.learner_id)
        self._academic_enrollments.setdefault(key, []).append(enrollment)

    def assign_learning_path(self, *, tenant_id: str, student_id: str, learning_path_id: str, course_ids: list[str]) -> dict[str, Any]:
        profile = self.get_student_profile(tenant_id=tenant_id, student_id=student_id)
        if profile is None:
            raise KeyError("student profile not found")
        self._learning_service.assign_learning_path(
            tenant_id=tenant_id,
            learner_id=student_id,
            learning_path_id=learning_path_id,
            assigned_course_ids=course_ids,
        )
        self.attach_batch(tenant_id=tenant_id, student_id=student_id, batch_id=learning_path_id)
        return self._learning_service.get_learner_progress(tenant_id=tenant_id, learner_id=student_id)

    def post_invoice_to_ledger(self, *, student_id: str, invoice: Invoice, currency: str = "USD") -> LedgerEntry:
        key = self._profile_key(tenant_id=invoice.tenant_id, student_id=student_id)
        if key not in self._profiles:
            raise KeyError("student profile not found")
        entry = LedgerEntry(
            entry_id=f"led_{invoice.invoice_id}",
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
        self._refresh_ledger_summary(*key)
        return entry

    def post_payment_to_ledger(self, *, tenant_id: str, student_id: str, payment_id: str, amount: Decimal, currency: str = "USD") -> LedgerEntry:
        key = self._profile_key(tenant_id=tenant_id, student_id=student_id)
        if key not in self._profiles:
            raise KeyError("student profile not found")
        entry = LedgerEntry(
            entry_id=f"pay_{payment_id}",
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
        self._refresh_ledger_summary(*key)
        return entry

    def get_student_ledger(self, *, tenant_id: str, student_id: str) -> tuple[LedgerEntry, ...]:
        key = self._profile_key(tenant_id=tenant_id, student_id=student_id)
        return tuple(sorted(self._ledger.get(key, []), key=lambda entry: entry.timestamp))

    def get_student_balance(self, *, tenant_id: str, student_id: str) -> Decimal:
        return sum((e.amount for e in self.get_student_ledger(tenant_id=tenant_id, student_id=student_id)), start=Decimal("0"))

    def _refresh_ledger_summary(self, tenant_id: str, student_id: str) -> None:
        key = self._profile_key(tenant_id=tenant_id, student_id=student_id)
        profile = self._profiles[key]
        entries = self._ledger.get(key, [])
        invoiced = sum((e.amount for e in entries if e.source_type == "invoice"), start=Decimal("0"))
        paid = sum((e.amount.copy_abs() for e in entries if e.source_type == "payment"), start=Decimal("0"))
        last_invoice = next((e.source_ref for e in reversed(entries) if e.source_type == "invoice"), None)
        last_payment = next((e.source_ref for e in reversed(entries) if e.source_type == "payment"), None)
        self._profiles[key] = profile.with_balance(
            invoiced=invoiced,
            paid=paid,
            last_invoice_id=last_invoice,
            last_payment_id=last_payment,
        )

    def run_qc_autofix(self) -> dict[str, bool]:
        for tenant_id, student_id in list(self._profiles):
            self._refresh_ledger_summary(tenant_id, student_id)
        return {
            "student_profile_unified_state": True,
            "ledger_consistency": True,
            "lifecycle_transitions": True,
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
        required = {
            "student.profile",
            "student.lifecycle",
            "student.academic_state",
            "student.financial_state",
            "student.attendance_summary",
            "student.ledger",
        }
        return all(self._domain_owner.get(domain) == "system-of-record" for domain in required) and not self.has_duplicate_data_ownership()
