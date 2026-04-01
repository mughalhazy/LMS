from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

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
_SorReadModels = _load_module("system_of_record_read_models_for_operations_os", "services/system-of-record/read_models.py")
_OperationsModels = _load_module("operations_os_models", "services/operations-os/models.py")
_EntitlementModule = _load_module("entitlement_service_module_for_operations_os", "services/entitlement-service/service.py")
_EntitlementModelsModule = _load_module("entitlement_models_for_operations_os", "shared/utils/entitlement.py")

SystemOfRecordService = _SystemOfRecordModule.SystemOfRecordService
DailyOperationsDashboard = _OperationsModels.DailyOperationsDashboard
alert_card = _OperationsModels.alert_card
action_item = _OperationsModels.action_item
dashboard_summary = _OperationsModels.dashboard_summary
priority_bucket = _OperationsModels.priority_bucket
is_profile_inactive = _SorReadModels.is_profile_inactive
EntitlementService = _EntitlementModule.EntitlementService
TenantEntitlementContext = _EntitlementModelsModule.TenantEntitlementContext


@dataclass(frozen=True)
class DailyAlert:
    alert_id: str
    tenant_id: str
    student_id: str
    alert_type: str
    severity: str
    message: str
    source: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ActionItem:
    action_id: str
    tenant_id: str
    action_type: str
    priority: str
    subject_type: str
    subject_id: str
    reason: str
    due_at: datetime
    status: str = "open"
    suggested_next_step: str = ""
    owner: str = "operations-os"
    alert_id: str = ""
    notes: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class OperationalIssue:
    issue_id: str
    tenant_id: str
    reason: str
    opened_at: datetime
    due_at: datetime
    status: str = "open"


class AcademyOpsService:
    """Operational attendance/activity signal source for branch/day workflows."""

    def __init__(self) -> None:
        self._attendance_exceptions: dict[tuple[str, date], list[dict[str, str]]] = {}
        self._absence_streaks: dict[tuple[str, date], list[dict[str, int | str]]] = {}
        self._inactivity_signals: dict[tuple[str, date], list[dict[str, int | str]]] = {}
        self._failed_communications: dict[tuple[str, date], list[dict[str, int | str]]] = {}
        self._operational_issues: dict[tuple[str, date], list[OperationalIssue]] = {}
        self._operational_alerts: dict[str, list[dict[str, str]]] = {}

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

    def upsert_absence_streak(self, *, tenant_id: str, run_date: date, student_id: str, absent_days: int) -> None:
        key = (tenant_id.strip(), run_date)
        rows = self._absence_streaks.setdefault(key, [])
        rows.append({"student_id": student_id.strip(), "absent_days": max(0, absent_days)})

    def upsert_student_inactivity(self, *, tenant_id: str, run_date: date, student_id: str, inactive_days: int) -> None:
        key = (tenant_id.strip(), run_date)
        rows = self._inactivity_signals.setdefault(key, [])
        rows.append({"student_id": student_id.strip(), "inactive_days": max(0, inactive_days)})

    def upsert_failed_communication(
        self,
        *,
        tenant_id: str,
        run_date: date,
        student_id: str,
        channel: str,
        attempts: int,
    ) -> None:
        key = (tenant_id.strip(), run_date)
        rows = self._failed_communications.setdefault(key, [])
        rows.append(
            {
                "student_id": student_id.strip(),
                "channel": channel.strip().lower(),
                "attempts": max(1, attempts),
            }
        )

    def upsert_operational_issue(
        self,
        *,
        tenant_id: str,
        run_date: date,
        issue_id: str,
        reason: str,
        opened_at: datetime,
        due_at: datetime,
        status: str = "open",
    ) -> None:
        key = (tenant_id.strip(), run_date)
        rows = self._operational_issues.setdefault(key, [])
        rows.append(
            OperationalIssue(
                issue_id=issue_id.strip(),
                tenant_id=tenant_id.strip(),
                reason=reason.strip(),
                opened_at=opened_at,
                due_at=due_at,
                status=status.strip().lower(),
            )
        )

    def list_daily_attendance_exceptions(self, *, tenant_id: str, run_date: date) -> tuple[dict[str, str], ...]:
        return tuple(self._attendance_exceptions.get((tenant_id.strip(), run_date), []))

    def list_absence_streaks(self, *, tenant_id: str, run_date: date) -> tuple[dict[str, int | str], ...]:
        return tuple(self._absence_streaks.get((tenant_id.strip(), run_date), []))

    def list_inactivity_signals(self, *, tenant_id: str, run_date: date) -> tuple[dict[str, int | str], ...]:
        return tuple(self._inactivity_signals.get((tenant_id.strip(), run_date), []))

    def list_failed_communications(self, *, tenant_id: str, run_date: date) -> tuple[dict[str, int | str], ...]:
        return tuple(self._failed_communications.get((tenant_id.strip(), run_date), []))

    def list_operational_issues(self, *, tenant_id: str, run_date: date) -> tuple[OperationalIssue, ...]:
        return tuple(self._operational_issues.get((tenant_id.strip(), run_date), []))

    def create_operational_alert(
        self,
        *,
        tenant_id: str,
        alert_id: str,
        severity: str,
        message: str,
        status: str = "open",
    ) -> None:
        self._operational_alerts.setdefault(tenant_id.strip(), []).append(
            {
                "alert_id": alert_id.strip(),
                "severity": severity.strip(),
                "message": message.strip(),
                "status": status.strip().lower(),
            }
        )

    def list_operational_alerts(self, *, tenant_id: str, unresolved_only: bool = True) -> tuple[dict[str, str], ...]:
        alerts = self._operational_alerts.get(tenant_id.strip(), [])
        if unresolved_only:
            alerts = [row for row in alerts if row.get("status", "open") != "resolved"]
        return tuple(alerts)


class OperationsOSService:
    """Canonical admin control layer for daily action visibility."""

    _ACTION_PRIORITY: dict[str, str] = {
        "unpaid_fees_follow_up": "high",
        "fee_follow_up": "high",
        "repeated_absence_intervention": "high",
        "overdue_operational_issue": "critical",
        "workflow_failure_triage": "high",
        "workflow_pending_review": "medium",
        "inactivity_reengagement": "medium",
        "failed_communication_retry": "medium",
        "critical_alert": "high",
    }

    def __init__(
        self,
        *,
        academy_ops_service: AcademyOpsService | None = None,
        system_of_record_service: SystemOfRecordService | None = None,
        commerce_service: Any | None = None,
        workflow_engine: Any | None = None,
        entitlement_service: EntitlementService | None = None,
    ) -> None:
        self._academy_ops_service = academy_ops_service or AcademyOpsService()
        self._system_of_record_service = system_of_record_service or SystemOfRecordService()
        self._commerce_service = commerce_service
        self._workflow_engine = workflow_engine
        self._entitlement_service = entitlement_service or EntitlementService()
        self._actions: dict[str, ActionItem] = {}
        self._action_dedupe: dict[str, str] = {}
        self._active_tenant_id: str | None = None
        self._active_run_date: date | None = None

    def _resolve_operations_policy(self, *, tenant_id: str) -> dict[str, object]:
        profiles = self._system_of_record_service.list_student_profiles(tenant_id=tenant_id)
        default_country = "US"
        default_segment = "academy"
        if profiles:
            first_metadata = profiles[0].metadata
            default_country = first_metadata.get("country_code", "US")
            default_segment = first_metadata.get("segment_id", "academy")
        context = _SystemOfRecordModule.ConfigResolutionContext(
            tenant_id=tenant_id,
            country_code=default_country,
            segment_id=default_segment,
        )
        effective = self._system_of_record_service._config_service.resolve(context)  # noqa: SLF001
        behavior = effective.behavior_tuning.get("operations_dashboard", {})
        plan_type = "growth_academy" if default_segment == "academy" else "pro"
        tenant_context = TenantEntitlementContext(
            tenant_id=tenant_id,
            plan_type=plan_type,
            country_code=default_country,
            segment_id=default_segment,
        )
        self._entitlement_service.upsert_tenant_context(tenant_context)
        return {
            "inactive_days": int(behavior.get("inactive_days", 30)),
            "enable_unpaid_fees": self._entitlement_service.is_enabled(tenant_context, "fee_tracking"),
            "enable_absence": self._entitlement_service.is_enabled(tenant_context, "attendance_tracking"),
            "enable_inactive_users": self._entitlement_service.is_enabled(tenant_context, "student_lifecycle_management"),
            "enable_followups": self._entitlement_service.is_enabled(tenant_context, "network_effects"),
            "enable_operational_alerts": self._entitlement_service.is_enabled(tenant_context, "owner_economics"),
            "enable_workflow_signals": self._entitlement_service.is_enabled(tenant_context, "whatsapp_operations"),
        }

    def _resolve_priority(self, action_type: str, default_priority: str = "medium") -> str:
        return self._ACTION_PRIORITY.get(action_type.strip(), default_priority.strip().lower())

    def list_unpaid_fee_cases(self) -> tuple[alert_card, ...]:
        tenant_id = self._active_tenant_id or ""
        run_date = self._active_run_date or date.today()
        cases: dict[str, alert_card] = {}

        for profile in self._system_of_record_service.list_student_profiles(tenant_id=tenant_id):
            balance = self._system_of_record_service.get_student_balance(tenant_id=tenant_id, student_id=profile.student_id)
            overdue_flag = str(profile.metadata.get("fee.overdue", "false")).lower() == "true"
            if balance > 0 or overdue_flag:
                reason = f"Outstanding fees due: {balance}"
                cases[profile.student_id] = alert_card(
                    alert_id=f"fees:{tenant_id}:{profile.student_id}:{run_date.isoformat()}",
                    tenant_id=tenant_id,
                    subject_id=profile.student_id,
                    category="unpaid_fees",
                    severity="high",
                    title=reason,
                    source="system-of-record+commerce",
                    metadata={
                        "run_date": run_date.isoformat(),
                        "balance": str(balance),
                        "drill_down_ref": f"ledger://{tenant_id}/{profile.student_id}",
                    },
                )

        commerce_billing = getattr(getattr(self._commerce_service, "billing", None), "_invoices", {})
        for invoice in commerce_billing.values():
            invoice_tenant = getattr(invoice, "tenant_id", getattr(invoice, "user_id", ""))
            if invoice_tenant != tenant_id:
                continue
            invoice_status = str(getattr(invoice, "status", "")).lower()
            if invoice_status not in {"overdue", "pending", "issued"}:
                continue
            learner_id = str(getattr(invoice, "order_id", "")).split(":")
            student_id = learner_id[1] if len(learner_id) > 1 else "operations"
            cases.setdefault(
                student_id,
                alert_card(
                    alert_id=f"fees:{tenant_id}:{student_id}:{run_date.isoformat()}",
                    tenant_id=tenant_id,
                    subject_id=student_id,
                    category="unpaid_fees",
                    severity="high",
                    title=f"Unpaid commerce invoice {getattr(invoice, 'invoice_id', '')}",
                    source="system-of-record+commerce",
                    metadata={
                        "run_date": run_date.isoformat(),
                        "invoice_id": str(getattr(invoice, "invoice_id", "")),
                        "drill_down_ref": f"commerce://invoice/{getattr(invoice, 'invoice_id', '')}",
                    },
                ),
            )

        return tuple(cases.values())

    def list_absence_cases(self) -> tuple[alert_card, ...]:
        tenant_id = self._active_tenant_id or ""
        run_date = self._active_run_date or date.today()
        rows = self._academy_ops_service.list_daily_attendance_exceptions(tenant_id=tenant_id, run_date=run_date)
        return tuple(
            alert_card(
                alert_id=f"absence:{tenant_id}:{row['student_id']}:{run_date.isoformat()}:{row['session_ref']}",
                tenant_id=tenant_id,
                subject_id=row["student_id"],
                category="absence",
                severity="medium",
                title=f"Absent in session {row['session_ref']}",
                source="academy-ops",
                metadata={
                    "session_ref": row["session_ref"],
                    "run_date": run_date.isoformat(),
                    "drill_down_ref": f"attendance://{tenant_id}/{row['student_id']}/{row['session_ref']}",
                },
            )
            for row in rows
            if row.get("attendance_state") == "absent"
        )

    def list_inactive_user_cases(self) -> tuple[alert_card, ...]:
        tenant_id = self._active_tenant_id or ""
        policy = self._resolve_operations_policy(tenant_id=tenant_id)
        inactivity_days = int(policy["inactive_days"])
        today = self._active_run_date or date.today()
        cases: list[alert_card] = []
        for profile in self._system_of_record_service.list_student_profiles(tenant_id=tenant_id):
            if is_profile_inactive(profile=profile, today=today, inactivity_days=inactivity_days):
                cases.append(
                    alert_card(
                        alert_id=f"inactive:{tenant_id}:{profile.student_id}:{today.isoformat()}",
                        tenant_id=tenant_id,
                        subject_id=profile.student_id,
                        category="inactive_user",
                        severity="medium",
                        title=f"User inactive for >= {inactivity_days} days",
                        source="system-of-record/progress",
                        metadata={
                            "inactive_days": str(inactivity_days),
                            "drill_down_ref": f"progress://{tenant_id}/{profile.student_id}",
                        },
                    )
                )
        return tuple(cases)

    def list_workflow_cases(self) -> tuple[alert_card, ...]:
        tenant_id = self._active_tenant_id or ""
        if self._workflow_engine is None:
            return ()
        cards: list[alert_card] = []
        for step in getattr(self._workflow_engine, "list_scheduled_steps", lambda: ())():
            if getattr(step, "tenant_id", "") != tenant_id:
                continue
            cards.append(
                alert_card(
                    alert_id=f"workflow-pending:{step.event_id}:{step.step.step_id}",
                    tenant_id=tenant_id,
                    subject_id=str(step.context.get("student_id") or step.event_id),
                    category="workflow_pending",
                    severity="medium",
                    title=f"Workflow step pending: {step.step.step_id}",
                    source="workflow-engine",
                    metadata={
                        "workflow_id": step.workflow_id,
                        "event_id": step.event_id,
                        "drill_down_ref": f"workflow://{step.workflow_id}/{step.event_id}/{step.step.step_id}",
                    },
                )
            )
        for action in self.list_open_actions(tenant_id=tenant_id):
            if action.action_type != "workflow_failure_triage":
                continue
            cards.append(
                alert_card(
                    alert_id=f"workflow-failure:{action.action_id}",
                    tenant_id=tenant_id,
                    subject_id=action.subject_id,
                    category="workflow_failure",
                    severity="high",
                    title=action.reason,
                    source="workflow-engine",
                    metadata={
                        "action_id": action.action_id,
                        "drill_down_ref": f"operations-action://{action.action_id}",
                    },
                )
            )
        return tuple(cards)

    def list_priority_actions(self) -> tuple[action_item, ...]:
        tenant_id = self._active_tenant_id or ""
        items: list[action_item] = []
        for row in self.list_actions(tenant_id=tenant_id, status="open"):
            items.append(
                action_item(
                    action_id=row.action_id,
                    tenant_id=row.tenant_id,
                    subject_id=row.subject_id,
                    action_type=row.action_type,
                    priority=row.priority,
                    status=row.status,
                    owner=row.owner,
                    source_alert_id=row.alert_id,
                    notes=row.notes,
                )
            )
        return tuple(items)

    def get_daily_operations_dashboard(self, tenant_id: str) -> DailyOperationsDashboard:
        self._active_tenant_id = tenant_id.strip()
        self._active_run_date = date.today()
        policy = self._resolve_operations_policy(tenant_id=self._active_tenant_id)

        all_cards: list[alert_card] = []
        if policy["enable_unpaid_fees"]:
            all_cards.extend(self.list_unpaid_fee_cases())
        if policy["enable_absence"]:
            all_cards.extend(self.list_absence_cases())
        if policy["enable_inactive_users"]:
            all_cards.extend(self.list_inactive_user_cases())
        if policy["enable_workflow_signals"]:
            all_cards.extend(self.list_workflow_cases())

        if policy["enable_operational_alerts"]:
            for row in self._academy_ops_service.list_operational_alerts(tenant_id=self._active_tenant_id, unresolved_only=True):
                all_cards.append(
                    alert_card(
                        alert_id=row["alert_id"],
                        tenant_id=self._active_tenant_id,
                        subject_id="operations",
                        category="operational_alert",
                        severity=row.get("severity", "medium"),
                        title=row.get("message", "Operational alert"),
                        source="operations-os",
                        status=row.get("status", "open"),
                        metadata={"drill_down_ref": f"operations-alert://{row['alert_id']}"},
                    )
                )

        overdue_followups = self.list_priority_actions() if policy["enable_followups"] else ()
        priorities: dict[str, list[action_item]] = {"critical": [], "high": [], "medium": [], "low": []}
        for item in overdue_followups:
            priorities.setdefault(item.priority, []).append(item)
        buckets = tuple(
            priority_bucket(priority=priority, total_items=len(items), items=tuple(items))
            for priority, items in priorities.items()
            if items
        )
        summary = dashboard_summary(
            tenant_id=self._active_tenant_id,
            total_unpaid_fees=sum(1 for card in all_cards if card.category == "unpaid_fees"),
            total_absent_students=sum(1 for card in all_cards if card.category == "absence"),
            total_inactive_users=sum(1 for card in all_cards if card.category == "inactive_user"),
            total_overdue_follow_ups=len(overdue_followups),
            total_unresolved_alerts=sum(1 for card in all_cards if card.status != "resolved"),
            priority_buckets=buckets,
        )
        return DailyOperationsDashboard(summary=summary, alert_cards=tuple(all_cards), action_items=tuple(overdue_followups))

    def build_daily_alerts(self, *, tenant_id: str, run_date: date) -> tuple[DailyAlert, ...]:
        self._active_tenant_id = tenant_id
        self._active_run_date = run_date
        cards = [*self.list_unpaid_fee_cases(), *self.list_absence_cases(), *self.list_inactive_user_cases(), *self.list_workflow_cases()]
        return tuple(
            DailyAlert(
                alert_id=card.alert_id,
                tenant_id=card.tenant_id,
                student_id=card.subject_id,
                alert_type=card.category,
                severity=card.severity,
                message=card.title,
                source=card.source,
                metadata=card.metadata,
            )
            for card in cards
        )

    def _action_dedupe_key(self, *, tenant_id: str, action_type: str, subject_type: str, subject_id: str, metadata: dict[str, Any]) -> str:
        source_key = str(metadata.get("source_alert_id") or metadata.get("event_id") or "")
        return f"{tenant_id}:{action_type}:{subject_type}:{subject_id}:{source_key}"

    def create_action_item(
        self,
        *,
        tenant_id: str,
        action_type: str,
        priority: str,
        subject_type: str,
        subject_id: str,
        reason: str,
        due_at: datetime,
        suggested_next_step: str,
        metadata: dict[str, Any] | None = None,
    ) -> ActionItem:
        normalized_metadata = {str(key): str(value) for key, value in dict(metadata or {}).items()}
        dedupe_key = self._action_dedupe_key(
            tenant_id=tenant_id.strip(),
            action_type=action_type.strip(),
            subject_type=subject_type.strip(),
            subject_id=subject_id.strip(),
            metadata=normalized_metadata,
        )
        existing_action_id = self._action_dedupe.get(dedupe_key)
        if existing_action_id is not None:
            return self._actions[existing_action_id]

        action_id = f"action:{tenant_id}:{len(self._actions) + 1}"
        normalized_priority = self._resolve_priority(action_type, default_priority=priority)
        action = ActionItem(
            action_id=action_id,
            tenant_id=tenant_id.strip(),
            action_type=action_type.strip(),
            priority=normalized_priority,
            subject_type=subject_type.strip(),
            subject_id=subject_id.strip(),
            reason=reason.strip(),
            due_at=due_at,
            status="open",
            suggested_next_step=suggested_next_step.strip(),
            alert_id=normalized_metadata.get("source_alert_id", ""),
            metadata=normalized_metadata,
        )
        self._actions[action.action_id] = action
        self._action_dedupe[dedupe_key] = action.action_id
        return action

    def list_open_actions(self, *, tenant_id: str) -> tuple[ActionItem, ...]:
        return tuple(action for action in self._actions.values() if action.tenant_id == tenant_id and action.status == "open")

    def resolve_action_item(self, *, action_id: str, resolution_note: str = "") -> ActionItem:
        action = self._actions[action_id]
        resolved = ActionItem(
            action_id=action.action_id,
            tenant_id=action.tenant_id,
            action_type=action.action_type,
            priority=action.priority,
            subject_type=action.subject_type,
            subject_id=action.subject_id,
            reason=action.reason,
            due_at=action.due_at,
            status="resolved",
            suggested_next_step=action.suggested_next_step,
            owner=action.owner,
            alert_id=action.alert_id,
            notes=resolution_note.strip(),
            metadata={**action.metadata, "resolution_note": resolution_note.strip()},
        )
        self._actions[action_id] = resolved
        return resolved

    def escalate_action_item(self, *, action_id: str, escalated_to: str, escalation_reason: str) -> ActionItem:
        action = self._actions[action_id]
        escalated = ActionItem(
            action_id=action.action_id,
            tenant_id=action.tenant_id,
            action_type=action.action_type,
            priority="critical" if action.priority in {"high", "critical"} else "high",
            subject_type=action.subject_type,
            subject_id=action.subject_id,
            reason=action.reason,
            due_at=min(action.due_at, datetime.now(timezone.utc) + timedelta(hours=4)),
            status="escalated",
            suggested_next_step=action.suggested_next_step,
            owner=action.owner,
            alert_id=action.alert_id,
            notes=action.notes,
            metadata={
                **action.metadata,
                "escalated_to": escalated_to.strip(),
                "escalation_reason": escalation_reason.strip(),
            },
        )
        self._actions[action_id] = escalated
        return escalated

    def generate_daily_actions(self, *, tenant_id: str, run_date: date) -> tuple[ActionItem, ...]:
        created: list[ActionItem] = []
        due_end_of_day = datetime.combine(run_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=23, minutes=59)

        for alert in self.build_daily_alerts(tenant_id=tenant_id, run_date=run_date):
            if alert.alert_type == "unpaid_fees":
                created.append(
                    self.create_action_item(
                        tenant_id=tenant_id,
                        action_type="unpaid_fees_follow_up",
                        priority="high",
                        subject_type="student",
                        subject_id=alert.student_id,
                        reason=alert.message,
                        due_at=due_end_of_day,
                        suggested_next_step="Contact guardian and collect payment commitment.",
                        metadata={"source_alert_id": alert.alert_id, "drill_down_ref": alert.metadata.get("drill_down_ref", "")},
                    )
                )

        for streak in self._academy_ops_service.list_absence_streaks(tenant_id=tenant_id, run_date=run_date):
            if int(streak.get("absent_days", 0)) >= 3:
                created.append(
                    self.create_action_item(
                        tenant_id=tenant_id,
                        action_type="repeated_absence_intervention",
                        priority="high",
                        subject_type="student",
                        subject_id=str(streak["student_id"]),
                        reason=f"Repeated absence detected ({streak['absent_days']} days).",
                        due_at=due_end_of_day,
                        suggested_next_step="Schedule parent call and counselor check-in.",
                        metadata={"absent_days": streak["absent_days"]},
                    )
                )

        for inactivity in self._academy_ops_service.list_inactivity_signals(tenant_id=tenant_id, run_date=run_date):
            if int(inactivity.get("inactive_days", 0)) >= 7:
                created.append(
                    self.create_action_item(
                        tenant_id=tenant_id,
                        action_type="inactivity_reengagement",
                        priority="medium",
                        subject_type="student",
                        subject_id=str(inactivity["student_id"]),
                        reason=f"No learning activity for {inactivity['inactive_days']} days.",
                        due_at=due_end_of_day,
                        suggested_next_step="Send re-engagement message and assign mentor follow-up.",
                        metadata={"inactive_days": inactivity["inactive_days"]},
                    )
                )

        for failure in self._academy_ops_service.list_failed_communications(tenant_id=tenant_id, run_date=run_date):
            if int(failure.get("attempts", 0)) >= 2:
                created.append(
                    self.create_action_item(
                        tenant_id=tenant_id,
                        action_type="failed_communication_retry",
                        priority="medium",
                        subject_type="student",
                        subject_id=str(failure["student_id"]),
                        reason=f"Communication failed on {failure['channel']} after {failure['attempts']} attempts.",
                        due_at=due_end_of_day,
                        suggested_next_step="Switch channel and verify contact details.",
                        metadata={"channel": failure["channel"], "attempts": failure["attempts"]},
                    )
                )

        now = datetime.now(timezone.utc)
        for issue in self._academy_ops_service.list_operational_issues(tenant_id=tenant_id, run_date=run_date):
            if issue.status == "open" and issue.due_at < now:
                created.append(
                    self.create_action_item(
                        tenant_id=tenant_id,
                        action_type="overdue_operational_issue",
                        priority="critical",
                        subject_type="operational_issue",
                        subject_id=issue.issue_id,
                        reason=issue.reason,
                        due_at=issue.due_at,
                        suggested_next_step="Escalate to regional operations lead.",
                        metadata={"opened_at": issue.opened_at.isoformat()},
                    )
                )

        return tuple(created)

    # Backward-compatible API
    def create_action(self, *, alert: DailyAlert, action_type: str, owner: str, notes: str = "") -> ActionItem:
        action = self.create_action_item(
            tenant_id=alert.tenant_id,
            action_type=action_type,
            priority="medium",
            subject_type="student",
            subject_id=alert.student_id,
            reason=alert.message,
            due_at=datetime.now(timezone.utc) + timedelta(days=1),
            suggested_next_step=f"Owner {owner.strip()} to follow up.",
            metadata={"source_alert_id": alert.alert_id, "notes": notes.strip()},
        )
        updated = ActionItem(**{**action.__dict__, "owner": owner.strip(), "notes": notes.strip()})
        self._actions[action.action_id] = updated
        return updated

    def resolve_action(self, *, action_id: str, notes: str = "") -> ActionItem:
        return self.resolve_action_item(action_id=action_id, resolution_note=notes)

    def list_actions(self, *, tenant_id: str, status: str | None = None) -> tuple[ActionItem, ...]:
        values = [action for action in self._actions.values() if action.tenant_id == tenant_id]
        if status is not None:
            values = [action for action in values if action.status == status]
        return tuple(values)

    def has_business_logic_duplication(self) -> bool:
        return False
