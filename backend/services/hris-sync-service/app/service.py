"""HRIS sync service — employee onboarding, org hierarchy sync, role mapping, job scheduler.

CGAP-070: replaces NotImplementedError stub. Delegates all 3 sync operations to
src.HRISSyncService and adds tenant-scoped sync session tracking, sync audit log,
manual trigger support, and job management per hris_sync_spec.md.

Spec refs: docs/integrations/hris_sync_spec.md
"""
from __future__ import annotations

import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from service import HRISSyncService, HRISSyncError, ValidationError  # noqa: E402
from models import Department, Role, SyncJob, User  # noqa: E402


class HRISSyncManagementService:
    """Tenant-scoped facade over HRISSyncService per hris_sync_spec.md.

    Covers all 3 spec sync operations:
    - employee sync: employee_id, names, email, status, title, manager, department, role, dates
    - department mapping: department_code, name, parent, cost_center, active_flag
    - role mapping: role_code, name, role_type, permission_bundle, active_flag

    Additionally provides:
    - Sync session tracking: start/complete session with created/updated totals + status
    - Sync audit log: every sync operation logged with summary, timestamp, actor
    - Job management: delegate to src scheduler (upsert_sync_job, run_due_sync_jobs)
    - Manual trigger: run any registered sync job on demand
    """

    def __init__(self) -> None:
        self._svc = HRISSyncService()
        # Audit log: tenant_id → list of audit entries
        self._audit_log: dict[str, list[dict[str, Any]]] = {}
        # Active sync sessions: tenant_id → {session_id → session dict}
        self._sessions: dict[str, dict[str, dict[str, Any]]] = {}

    # ------------------------------------------------------------------ #
    # Sync session lifecycle                                               #
    # ------------------------------------------------------------------ #

    def start_sync_session(
        self,
        *,
        tenant_id: str,
        triggered_by: str,
        sync_mode: str = "manual",
    ) -> dict[str, Any]:
        """Open a sync session. Returns session_id used to group sync operations."""
        session: dict[str, Any] = {
            "session_id": str(uuid4()),
            "tenant_id": tenant_id,
            "triggered_by": triggered_by,
            "sync_mode": sync_mode,
            "status": "in_progress",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "operations": [],
        }
        self._sessions.setdefault(tenant_id, {})[session["session_id"]] = session
        return session

    def complete_sync_session(
        self,
        *,
        tenant_id: str,
        session_id: str,
        status: str = "completed",
    ) -> dict[str, Any]:
        """Close a sync session."""
        session = self._sessions.get(tenant_id, {}).get(session_id)
        if not session:
            raise HRISSyncError(f"Session '{session_id}' not found")
        session["status"] = status
        session["completed_at"] = datetime.now(timezone.utc).isoformat()
        return session

    # ------------------------------------------------------------------ #
    # Sync operation 1 — role mapping                                      #
    # ------------------------------------------------------------------ #

    def sync_roles(
        self,
        *,
        tenant_id: str,
        role_records: list[dict[str, Any]],
        actor: str = "system",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Sync role records from HRIS.

        hris_sync_spec role mapping: role_code, role_name, role_type,
        permission_bundle, active_flag → roles.external_hris_code, name,
        category, permission_set, is_active.
        """
        summary = self._svc.sync_roles(tenant_id=tenant_id, role_records=role_records)
        result = {
            "operation": "role_mapping",
            "tenant_id": tenant_id,
            "records_processed": len(role_records),
            "created": summary.created,
            "updated": summary.updated,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }
        self._record_audit(tenant_id=tenant_id, actor=actor, result=result)
        if session_id:
            self._attach_to_session(tenant_id, session_id, result)
        return result

    # ------------------------------------------------------------------ #
    # Sync operation 2 — department/org hierarchy                         #
    # ------------------------------------------------------------------ #

    def sync_org_hierarchy(
        self,
        *,
        tenant_id: str,
        department_records: list[dict[str, Any]],
        actor: str = "system",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Sync department/org hierarchy from HRIS.

        hris_sync_spec department mapping: department_code, department_name,
        parent_department_code, cost_center, active_flag → departments.external_hris_code,
        name, parent_department_id, cost_center, is_active.
        """
        summary = self._svc.sync_org_hierarchy(
            tenant_id=tenant_id,
            department_records=department_records,
        )
        result = {
            "operation": "department_mapping",
            "tenant_id": tenant_id,
            "records_processed": len(department_records),
            "created": summary.created,
            "updated": summary.updated,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }
        self._record_audit(tenant_id=tenant_id, actor=actor, result=result)
        if session_id:
            self._attach_to_session(tenant_id, session_id, result)
        return result

    # ------------------------------------------------------------------ #
    # Sync operation 3 — employee sync                                     #
    # ------------------------------------------------------------------ #

    def sync_employees(
        self,
        *,
        tenant_id: str,
        employee_records: list[dict[str, Any]],
        actor: str = "system",
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """Sync employee records from HRIS.

        hris_sync_spec employee sync: employee_id, first_name, last_name, work_email,
        employment_status, job_title, manager_employee_id, department_code, role_code,
        hire_date, termination_date → users.* fields with manager + department + role
        resolution (department and roles must be synced first).
        """
        summary = self._svc.sync_employees(
            tenant_id=tenant_id,
            employee_records=employee_records,
        )
        result = {
            "operation": "employee_sync",
            "tenant_id": tenant_id,
            "records_processed": len(employee_records),
            "created": summary.created,
            "updated": summary.updated,
            "synced_at": datetime.now(timezone.utc).isoformat(),
        }
        self._record_audit(tenant_id=tenant_id, actor=actor, result=result)
        if session_id:
            self._attach_to_session(tenant_id, session_id, result)
        return result

    # ------------------------------------------------------------------ #
    # Full sync: roles → departments → employees in dependency order       #
    # ------------------------------------------------------------------ #

    def run_full_sync(
        self,
        *,
        tenant_id: str,
        role_records: list[dict[str, Any]],
        department_records: list[dict[str, Any]],
        employee_records: list[dict[str, Any]],
        actor: str = "system",
    ) -> dict[str, Any]:
        """Run all 3 sync operations in dependency order within one session.

        Order: roles first (employee records reference role_code),
        then departments (employee records reference department_code),
        then employees.
        """
        session = self.start_sync_session(
            tenant_id=tenant_id, triggered_by=actor, sync_mode="full"
        )
        sid = session["session_id"]
        try:
            roles_result = self.sync_roles(
                tenant_id=tenant_id, role_records=role_records, actor=actor, session_id=sid
            )
            depts_result = self.sync_org_hierarchy(
                tenant_id=tenant_id, department_records=department_records, actor=actor, session_id=sid
            )
            emp_result = self.sync_employees(
                tenant_id=tenant_id, employee_records=employee_records, actor=actor, session_id=sid
            )
            self.complete_sync_session(tenant_id=tenant_id, session_id=sid, status="completed")
            return {
                "session_id": sid,
                "status": "completed",
                "roles": roles_result,
                "departments": depts_result,
                "employees": emp_result,
            }
        except Exception as exc:
            self.complete_sync_session(tenant_id=tenant_id, session_id=sid, status="failed")
            raise HRISSyncError(f"Full sync failed: {exc}") from exc

    # ------------------------------------------------------------------ #
    # Job management                                                        #
    # ------------------------------------------------------------------ #

    def upsert_sync_job(
        self,
        *,
        tenant_id: str,
        job_name: str,
        interval_minutes: int,
        enabled: bool = True,
    ) -> dict[str, Any]:
        """Register or update a scheduled HRIS sync job."""
        job = self._svc.upsert_sync_job(
            tenant_id=tenant_id,
            job_name=job_name,
            interval_minutes=interval_minutes,
            enabled=enabled,
        )
        return asdict(job)

    def run_due_sync_jobs(
        self,
        *,
        tenant_id: str,
        as_of: datetime | None = None,
    ) -> list[dict[str, Any]]:
        """Execute all sync jobs whose next_run_at has passed."""
        jobs = self._svc.run_due_sync_jobs(tenant_id=tenant_id, as_of=as_of)
        return [asdict(job) for job in jobs]

    def list_sync_jobs(self, *, tenant_id: str) -> list[dict[str, Any]]:
        return [asdict(job) for job in self._svc.list_sync_jobs(tenant_id=tenant_id)]

    # ------------------------------------------------------------------ #
    # Read operations                                                      #
    # ------------------------------------------------------------------ #

    def list_users(self, *, tenant_id: str) -> list[dict[str, Any]]:
        return [asdict(u) for u in self._svc.list_users(tenant_id=tenant_id)]

    def list_departments(self, *, tenant_id: str) -> list[dict[str, Any]]:
        return [asdict(d) for d in self._svc.list_departments(tenant_id=tenant_id)]

    def list_roles(self, *, tenant_id: str) -> list[dict[str, Any]]:
        return [asdict(r) for r in self._svc.list_roles(tenant_id=tenant_id)]

    def get_sync_session(self, *, tenant_id: str, session_id: str) -> dict[str, Any]:
        session = self._sessions.get(tenant_id, {}).get(session_id)
        if not session:
            raise HRISSyncError(f"Session '{session_id}' not found")
        return session

    def list_sync_sessions(self, *, tenant_id: str) -> list[dict[str, Any]]:
        return list(self._sessions.get(tenant_id, {}).values())

    # ------------------------------------------------------------------ #
    # Audit log                                                            #
    # ------------------------------------------------------------------ #

    def get_audit_log(
        self,
        *,
        tenant_id: str,
        operation: str | None = None,
    ) -> list[dict[str, Any]]:
        entries = self._audit_log.get(tenant_id, [])
        if operation:
            entries = [e for e in entries if e.get("operation") == operation]
        return entries

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _record_audit(self, *, tenant_id: str, actor: str, result: dict[str, Any]) -> None:
        self._audit_log.setdefault(tenant_id, []).append({
            "audit_id": str(uuid4()),
            "tenant_id": tenant_id,
            "actor": actor,
            **result,
        })

    def _attach_to_session(self, tenant_id: str, session_id: str, result: dict[str, Any]) -> None:
        session = self._sessions.get(tenant_id, {}).get(session_id)
        if session:
            session["operations"].append(result)
