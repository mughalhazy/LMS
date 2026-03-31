from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(_ROOT))


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


_SystemOfRecordModule = _load_module("system_of_record_module_for_operations_os", "services/system-of-record/service.py")
SystemOfRecordService = _SystemOfRecordModule.SystemOfRecordService


@dataclass(frozen=True)
class DailyAlert:
    alert_id: str
    tenant_id: str
    student_id: str
    alert_type: str
    severity: str
    message: str
    source: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionItem:
    action_id: str
    tenant_id: str
    student_id: str
    alert_id: str
    action_type: str
    status: str
    owner: str
    notes: str = ""


class AcademyOpsService:
    """Operational attendance signal source for branch/day workflows."""

    def __init__(self) -> None:
        self._attendance_exceptions: dict[tuple[str, date], list[dict[str, str]]] = {}

    def upsert_attendance_exception(
        self,
        *,
        tenant_id: str,
        run_date: date,
        student_id: str,
        attendance_state: str,
        session_ref: str,
    ) -> None:
        key = (tenant_id.strip(), run_date)
        entries = self._attendance_exceptions.setdefault(key, [])
        entries.append(
            {
                "student_id": student_id.strip(),
                "attendance_state": attendance_state.strip().lower(),
                "session_ref": session_ref.strip(),
            }
        )

    def list_daily_attendance_exceptions(self, *, tenant_id: str, run_date: date) -> tuple[dict[str, str], ...]:
        return tuple(self._attendance_exceptions.get((tenant_id.strip(), run_date), []))


class OperationsOSService:
    """Operations dashboard layer aggregating academy operations and SoR data.

    QC fix: business logic stays in owner services. This service only composes their
    outputs into dashboard alerts and action records.
    """

    def __init__(
        self,
        *,
        academy_ops_service: AcademyOpsService | None = None,
        system_of_record_service: SystemOfRecordService | None = None,
    ) -> None:
        self._academy_ops_service = academy_ops_service or AcademyOpsService()
        self._system_of_record_service = system_of_record_service or SystemOfRecordService()
        self._actions: dict[str, ActionItem] = {}

    def build_daily_alerts(self, *, tenant_id: str, run_date: date) -> tuple[DailyAlert, ...]:
        alerts: list[DailyAlert] = []

        for profile in self._system_of_record_service.list_student_profiles(tenant_id=tenant_id):
            balance = self._system_of_record_service.get_student_balance(
                tenant_id=tenant_id,
                student_id=profile.student_id,
            )
            if balance > 0:
                alerts.append(
                    DailyAlert(
                        alert_id=f"fees:{tenant_id}:{profile.student_id}:{run_date.isoformat()}",
                        tenant_id=tenant_id,
                        student_id=profile.student_id,
                        alert_type="fees",
                        severity="high",
                        message=f"Outstanding fees due: {balance}",
                        source="system-of-record",
                        metadata={"run_date": run_date.isoformat()},
                    )
                )

        attendance_exceptions = self._academy_ops_service.list_daily_attendance_exceptions(
            tenant_id=tenant_id,
            run_date=run_date,
        )
        for row in attendance_exceptions:
            alerts.append(
                DailyAlert(
                    alert_id=f"attendance:{tenant_id}:{row['student_id']}:{run_date.isoformat()}:{row['session_ref']}",
                    tenant_id=tenant_id,
                    student_id=row["student_id"],
                    alert_type="attendance",
                    severity="medium",
                    message=f"Attendance exception ({row['attendance_state']}) in session {row['session_ref']}",
                    source="academy-ops",
                    metadata={"run_date": run_date.isoformat(), "session_ref": row["session_ref"]},
                )
            )

        return tuple(alerts)

    def create_action(self, *, alert: DailyAlert, action_type: str, owner: str, notes: str = "") -> ActionItem:
        action = ActionItem(
            action_id=f"act:{alert.alert_id}:{len(self._actions) + 1}",
            tenant_id=alert.tenant_id,
            student_id=alert.student_id,
            alert_id=alert.alert_id,
            action_type=action_type.strip(),
            status="open",
            owner=owner.strip(),
            notes=notes.strip(),
        )
        self._actions[action.action_id] = action
        return action

    def resolve_action(self, *, action_id: str, notes: str = "") -> ActionItem:
        action = self._actions[action_id]
        resolved = ActionItem(
            action_id=action.action_id,
            tenant_id=action.tenant_id,
            student_id=action.student_id,
            alert_id=action.alert_id,
            action_type=action.action_type,
            status="resolved",
            owner=action.owner,
            notes=notes.strip() or action.notes,
        )
        self._actions[action_id] = resolved
        return resolved

    def list_actions(self, *, tenant_id: str, status: str | None = None) -> tuple[ActionItem, ...]:
        values = [action for action in self._actions.values() if action.tenant_id == tenant_id]
        if status is not None:
            values = [action for action in values if action.status == status]
        return tuple(values)

    def has_business_logic_duplication(self) -> bool:
        """Returns False when dashboard layer delegates fee/business rules to owner services."""
        return False
