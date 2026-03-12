from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Iterable, List, Optional

from .models import Department, Role, SyncJob, User


class HRISSyncError(Exception):
    """Base exception for HRIS sync operations."""


class ValidationError(HRISSyncError):
    """Raised when incoming data violates sync constraints."""


@dataclass
class SyncSummary:
    operation: str
    created: int = 0
    updated: int = 0


class HRISSyncService:
    """In-memory HRIS sync service handling employee/org/role synchronization and jobs."""

    def __init__(self) -> None:
        self._roles_by_tenant_and_code: Dict[tuple[str, str], Role] = {}
        self._departments_by_tenant_and_code: Dict[tuple[str, str], Department] = {}
        self._users_by_tenant_and_external_id: Dict[tuple[str, str], User] = {}
        self._jobs_by_tenant_and_name: Dict[tuple[str, str], SyncJob] = {}

    def sync_roles(self, *, tenant_id: str, role_records: Iterable[dict]) -> SyncSummary:
        summary = SyncSummary(operation="role mapping")

        for record in role_records:
            role_code = self._required(record, "role_code")
            key = (tenant_id, role_code)
            role = self._roles_by_tenant_and_code.get(key)

            if role is None:
                role = Role(
                    tenant_id=tenant_id,
                    external_hris_code=role_code,
                    name=self._required(record, "role_name"),
                    category=self._required(record, "role_type"),
                    permission_set=dict(record.get("permission_bundle") or {}),
                    is_active=bool(record.get("active_flag", True)),
                )
                self._roles_by_tenant_and_code[key] = role
                summary.created += 1
            else:
                role.name = self._required(record, "role_name")
                role.category = self._required(record, "role_type")
                role.permission_set = dict(record.get("permission_bundle") or {})
                role.is_active = bool(record.get("active_flag", True))
                role.updated_at = self._now()
                summary.updated += 1

        return summary

    def sync_org_hierarchy(self, *, tenant_id: str, department_records: Iterable[dict]) -> SyncSummary:
        summary = SyncSummary(operation="org hierarchy sync")

        normalized_records = list(department_records)
        for record in normalized_records:
            code = self._required(record, "department_code")
            key = (tenant_id, code)
            department = self._departments_by_tenant_and_code.get(key)

            if department is None:
                department = Department(
                    tenant_id=tenant_id,
                    external_hris_code=code,
                    name=self._required(record, "department_name"),
                    cost_center=record.get("cost_center"),
                    parent_external_hris_code=record.get("parent_department_code"),
                    is_active=bool(record.get("active_flag", True)),
                )
                self._departments_by_tenant_and_code[key] = department
                summary.created += 1
            else:
                department.name = self._required(record, "department_name")
                department.cost_center = record.get("cost_center")
                department.parent_external_hris_code = record.get("parent_department_code")
                department.is_active = bool(record.get("active_flag", True))
                department.updated_at = self._now()
                summary.updated += 1

        for record in normalized_records:
            code = self._required(record, "department_code")
            parent_code = record.get("parent_department_code")
            department = self._departments_by_tenant_and_code[(tenant_id, code)]

            if not parent_code:
                department.parent_department_id = None
                continue

            parent = self._departments_by_tenant_and_code.get((tenant_id, parent_code))
            if parent is None:
                raise ValidationError(
                    f"department '{code}' references missing parent_department_code '{parent_code}'"
                )
            if parent.department_id == department.department_id:
                raise ValidationError("department cannot reference itself as parent")

            department.parent_department_id = parent.department_id
            department.updated_at = self._now()

        return summary

    def sync_employees(self, *, tenant_id: str, employee_records: Iterable[dict]) -> SyncSummary:
        summary = SyncSummary(operation="employee sync")
        records = list(employee_records)

        for record in records:
            external_id = self._required(record, "employee_id")
            key = (tenant_id, external_id)
            user = self._users_by_tenant_and_external_id.get(key)

            mapped_department_id = self._resolve_department_id(
                tenant_id=tenant_id,
                department_code=record.get("department_code"),
            )
            mapped_role_id = self._resolve_role_id(
                tenant_id=tenant_id,
                role_code=record.get("role_code"),
            )

            if user is None:
                user = User(
                    tenant_id=tenant_id,
                    external_hris_id=external_id,
                    first_name=self._required(record, "first_name"),
                    last_name=self._required(record, "last_name"),
                    email=self._required(record, "work_email"),
                    status=self._required(record, "employment_status"),
                    title=self._required(record, "job_title"),
                    manager_user_id=None,
                    department_id=mapped_department_id,
                    role_id=mapped_role_id,
                    hire_date=self._parse_optional_datetime(record.get("hire_date")),
                    deactivated_at=self._parse_optional_datetime(record.get("termination_date")),
                )
                self._users_by_tenant_and_external_id[key] = user
                summary.created += 1
            else:
                user.first_name = self._required(record, "first_name")
                user.last_name = self._required(record, "last_name")
                user.email = self._required(record, "work_email")
                user.status = self._required(record, "employment_status")
                user.title = self._required(record, "job_title")
                user.department_id = mapped_department_id
                user.role_id = mapped_role_id
                user.hire_date = self._parse_optional_datetime(record.get("hire_date"))
                user.deactivated_at = self._parse_optional_datetime(record.get("termination_date"))
                user.updated_at = self._now()
                summary.updated += 1

        for record in records:
            external_id = self._required(record, "employee_id")
            user = self._users_by_tenant_and_external_id[(tenant_id, external_id)]
            manager_external_id = record.get("manager_employee_id")
            if manager_external_id:
                manager = self._users_by_tenant_and_external_id.get((tenant_id, manager_external_id))
                if manager:
                    user.manager_user_id = manager.user_id
                elif manager_external_id == external_id:
                    raise ValidationError("employee cannot be configured as their own manager")
                else:
                    user.manager_user_id = None
            else:
                user.manager_user_id = None
            user.updated_at = self._now()

        return summary

    def upsert_sync_job(self, *, tenant_id: str, job_name: str, interval_minutes: int, enabled: bool = True) -> SyncJob:
        if interval_minutes <= 0:
            raise ValidationError("interval_minutes must be greater than 0")

        key = (tenant_id, job_name)
        now = self._now()
        job = self._jobs_by_tenant_and_name.get(key)

        if job is None:
            job = SyncJob(
                tenant_id=tenant_id,
                job_name=job_name,
                interval_minutes=interval_minutes,
                enabled=enabled,
                next_run_at=now + timedelta(minutes=interval_minutes) if enabled else None,
            )
            self._jobs_by_tenant_and_name[key] = job
            return job

        job.interval_minutes = interval_minutes
        job.enabled = enabled
        job.updated_at = now
        if enabled and job.next_run_at is None:
            job.next_run_at = now + timedelta(minutes=interval_minutes)
        if not enabled:
            job.next_run_at = None
        return job

    def run_due_sync_jobs(self, *, tenant_id: str, as_of: Optional[datetime] = None) -> List[SyncJob]:
        now = as_of or self._now()
        executed: List[SyncJob] = []

        for (job_tenant_id, _), job in self._jobs_by_tenant_and_name.items():
            if job_tenant_id != tenant_id:
                continue
            if not job.enabled or job.next_run_at is None:
                continue
            if job.next_run_at <= now:
                job.last_run_at = now
                job.next_run_at = now + timedelta(minutes=job.interval_minutes)
                job.updated_at = now
                executed.append(job)

        return executed

    def list_users(self, *, tenant_id: str) -> List[User]:
        return [user for (user_tenant_id, _), user in self._users_by_tenant_and_external_id.items() if user_tenant_id == tenant_id]

    def list_departments(self, *, tenant_id: str) -> List[Department]:
        return [
            department
            for (department_tenant_id, _), department in self._departments_by_tenant_and_code.items()
            if department_tenant_id == tenant_id
        ]

    def list_roles(self, *, tenant_id: str) -> List[Role]:
        return [role for (role_tenant_id, _), role in self._roles_by_tenant_and_code.items() if role_tenant_id == tenant_id]

    def list_sync_jobs(self, *, tenant_id: str) -> List[SyncJob]:
        return [job for (job_tenant_id, _), job in self._jobs_by_tenant_and_name.items() if job_tenant_id == tenant_id]

    def _resolve_department_id(self, *, tenant_id: str, department_code: Optional[str]) -> Optional[str]:
        if not department_code:
            return None
        department = self._departments_by_tenant_and_code.get((tenant_id, department_code))
        if not department:
            raise ValidationError(f"department_code '{department_code}' is not mapped")
        return department.department_id

    def _resolve_role_id(self, *, tenant_id: str, role_code: Optional[str]) -> Optional[str]:
        if not role_code:
            return None
        role = self._roles_by_tenant_and_code.get((tenant_id, role_code))
        if not role:
            raise ValidationError(f"role_code '{role_code}' is not mapped")
        return role.role_id

    @staticmethod
    def _required(record: dict, field_name: str) -> str:
        value = record.get(field_name)
        if value is None:
            raise ValidationError(f"missing required field '{field_name}'")
        if isinstance(value, str) and not value.strip():
            raise ValidationError(f"field '{field_name}' cannot be blank")
        return str(value)

    @staticmethod
    def _parse_optional_datetime(value: Optional[str]) -> Optional[datetime]:
        if value in (None, ""):
            return None
        normalized = str(value).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)
