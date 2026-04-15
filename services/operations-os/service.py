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

SystemOfRecordService = _SystemOfRecordModule.SystemOfRecordService
DailyOperationsDashboard = _OperationsModels.DailyOperationsDashboard
alert_card = _OperationsModels.alert_card
action_item = _OperationsModels.action_item
dashboard_summary = _OperationsModels.dashboard_summary
priority_bucket = _OperationsModels.priority_bucket
is_profile_inactive = _SorReadModels.is_profile_inactive


def _format_pattern(pattern: str, implication: str, suggested_action: str) -> str:
    """BC-OPS-01: canonical formatted output for an OperationalPattern."""
    return f"Pattern: {pattern} / Implication: {implication} / Suggested action: {suggested_action}"


@dataclass(frozen=True)
class OperationalPattern:
    """BC-OPS-01: structured output for a detected operational trend/pattern.

    Contains exactly what BC-OPS-01 requires:
      Pattern: what was detected (with magnitude)
      Implication: what this means for the operator
      Suggested action: specific next step with optional one-click trigger ref
    """
    tenant_id: str
    pattern: str
    implication: str
    suggested_action: str
    severity: str          # "critical" | "high" | "medium"
    signal_type: str       # "fees" | "attendance" | "inactivity" | "enrollment"
    trigger_ref: str = ""  # optional one-click action reference
    # BC-OPS-01: pre-formatted "Pattern: [...] / Implication: [...] / Suggested action: [...]"
    formatted_output: str = ""


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

    # BC-OPS-02: action types that are informational only (OPTIONAL tier)
    _OPTIONAL_ACTION_TYPES: frozenset[str] = frozenset({
        "workflow_pending_review",
        "failed_communication_retry",
    })

    # BC-OPS-02: maps internal priority → three-tier label (CRITICAL/IMPORTANT/OPTIONAL)
    _TIER_MAP: dict[str, str] = {
        "critical": "CRITICAL",   # action today
        "high": "IMPORTANT",      # action within 48h
        "medium": "IMPORTANT",
        "low": "OPTIONAL",        # insight only
        "optional": "OPTIONAL",
    }

    def __init__(
        self,
        *,
        academy_ops_service: AcademyOpsService | None = None,
        system_of_record_service: SystemOfRecordService | None = None,
        commerce_service: Any | None = None,
        workflow_engine: Any | None = None,
        notification_service: Any | None = None,
    ) -> None:
        self._academy_ops_service = academy_ops_service or AcademyOpsService()
        self._system_of_record_service = system_of_record_service or SystemOfRecordService()
        self._commerce_service = commerce_service
        self._workflow_engine = workflow_engine
        self._notification_service = notification_service
        self._actions: dict[str, ActionItem] = {}
        self._action_dedupe: dict[str, str] = {}
        self._active_tenant_id: str | None = None
        self._active_run_date: date | None = None
        # BC-OPS-01: prior-period signal counts for trend detection.
        # Keys: (tenant_id, period_key) → {signal_type: count}
        self._period_snapshots: dict[tuple[str, str], dict[str, int]] = {}
        # BC-OPS-03: scheduled daily delivery registrations
        self._scheduled_deliveries: list[dict] = []

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
        return {
            "inactive_days": int(behavior.get("inactive_days", 30)),
            "enable_unpaid_fees": bool(effective.capability_enabled.get("operations.unpaid_fees", True)),
            "enable_absence": bool(effective.capability_enabled.get("operations.absence", True)),
            "enable_inactive_users": bool(effective.capability_enabled.get("operations.inactive_users", True)),
            "enable_followups": bool(effective.capability_enabled.get("operations.followups", True)),
            "enable_operational_alerts": bool(effective.capability_enabled.get("operations.operational_alerts", True)),
            "enable_workflow_signals": bool(effective.capability_enabled.get("operations.workflow_signals", True)),
            # BC-OPS-02: config-driven tier thresholds
            "critical_fee_pct_threshold": int(behavior.get("critical_fee_pct_threshold", 50)),
            "important_absence_pct_threshold": int(behavior.get("important_absence_pct_threshold", 10)),
        }

    def _resolve_priority(self, action_type: str, default_priority: str = "medium") -> str:
        return self._ACTION_PRIORITY.get(action_type.strip(), default_priority.strip().lower())

    def _resolve_action_tier(self, action_type: str, tenant_id: str) -> str:
        """BC-OPS-02: resolve BC tier (CRITICAL/IMPORTANT/OPTIONAL) for an action type."""
        if action_type in self._OPTIONAL_ACTION_TYPES:
            priority = "optional"
        else:
            priority = self._resolve_priority(action_type)
        return self._TIER_MAP.get(priority, "OPTIONAL")

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

    def receive_operational_event(self, envelope: dict[str, Any]) -> None:
        """Receive a canonical event envelope and route to the appropriate operational handler.

        Entry point for OperationsOSForwarder (CGAP-020). Routes incoming domain events
        to action items and academy-ops signal records per BC-OPS-01 proactive detection contract.

        References: operations_os_spec.md BC-OPS-01, BC-OPS-02
        """
        event_type = str(envelope.get("event_type", "")).strip().lower()
        tenant_id = str(envelope.get("tenant_id", "")).strip()
        payload = dict(envelope.get("payload") or {})
        event_id = str(envelope.get("event_id", ""))

        if not tenant_id or not event_type:
            return

        if event_type in {"fee.overdue", "fee.due", "payment.missed", "payment.overdue"}:
            student_id = str(payload.get("student_id") or payload.get("user_id") or "unknown")
            overdue_days = int(payload.get("overdue_days", 0))
            amount = payload.get("amount")
            reason = "Fee overdue" if "overdue" in event_type else "Fee due"
            if overdue_days:
                reason = f"{reason} — {overdue_days} days outstanding"
            if amount:
                reason = f"{reason} (amount: {amount})"
            self.create_action_item(
                tenant_id=tenant_id,
                action_type="unpaid_fees_follow_up",
                priority="high",
                subject_type="student",
                subject_id=student_id,
                reason=reason,
                due_at=datetime.now(timezone.utc) + timedelta(hours=24),
                suggested_next_step="Contact guardian and confirm payment plan.",
                metadata={"event_id": event_id, "event_type": event_type},
            )

        elif event_type == "attendance.marked":
            student_id = str(payload.get("student_id") or "unknown")
            attendance_status = str(
                payload.get("attendance_status") or payload.get("status") or "absent"
            ).strip().lower()
            session_ref = str(payload.get("session_ref") or payload.get("session_id") or event_id)
            run_date = date.today()
            if isinstance(payload.get("session_date"), str):
                try:
                    run_date = date.fromisoformat(payload["session_date"])
                except ValueError:
                    pass
            self._academy_ops_service.upsert_attendance_exception(
                tenant_id=tenant_id,
                run_date=run_date,
                student_id=student_id,
                attendance_state=attendance_status,
                session_ref=session_ref,
            )
            if attendance_status == "absent":
                self.create_action_item(
                    tenant_id=tenant_id,
                    action_type="repeated_absence_intervention",
                    priority="medium",
                    subject_type="student",
                    subject_id=student_id,
                    reason="Absence recorded in session.",
                    due_at=datetime.now(timezone.utc) + timedelta(hours=48),
                    suggested_next_step="Check absence streak and contact guardian if threshold approaching.",
                    metadata={"event_id": event_id, "session_ref": session_ref},
                )

        elif event_type in {"user_inactive", "learner.inactivity_threshold_crossed"}:
            student_id = str(payload.get("student_id") or payload.get("user_id") or "unknown")
            inactive_days = int(payload.get("inactive_days", 7))
            self.create_action_item(
                tenant_id=tenant_id,
                action_type="inactivity_reengagement",
                priority="medium",
                subject_type="student",
                subject_id=student_id,
                reason=f"Learner inactive for {inactive_days} days.",
                due_at=datetime.now(timezone.utc) + timedelta(hours=48),
                suggested_next_step="Send nudge notification and assign mentor check-in.",
                metadata={"event_id": event_id, "inactive_days": str(inactive_days)},
            )

        elif event_type == "communication.failed":
            student_id = str(payload.get("student_id") or payload.get("user_id") or "unknown")
            channel = str(payload.get("channel") or "unknown")
            attempts = int(payload.get("attempts", 1))
            self._academy_ops_service.upsert_failed_communication(
                tenant_id=tenant_id,
                run_date=date.today(),
                student_id=student_id,
                channel=channel,
                attempts=attempts,
            )
            self.create_action_item(
                tenant_id=tenant_id,
                action_type="failed_communication_retry",
                priority="medium",
                subject_type="student",
                subject_id=student_id,
                reason=f"Communication failed on {channel} after {attempts} attempt(s).",
                due_at=datetime.now(timezone.utc) + timedelta(hours=24),
                suggested_next_step="Try alternate channel and verify contact info.",
                metadata={"event_id": event_id, "channel": channel},
            )

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

    def generate_daily_action_list_document(self, *, tenant_id: str, run_date: date | None = None) -> str:
        """Return a BC-OPS-03 formatted Action List document for delivery via message channel.

        Produces a structured text document with labelled sections:
        CRITICAL / IMPORTANT / PAYMENTS / ATTENDANCE / INACTIVE USERS.
        Each section lists only the action items that belong to it; empty sections are omitted.

        CGAP-015 fix: generate_daily_actions() previously returned raw ActionItem tuples with no
        formatting.  This method converts them into a deliverable document per BC-OPS-03.
        """
        effective_date = run_date or date.today()
        actions = self.generate_daily_actions(tenant_id=tenant_id, run_date=effective_date)

        # Bucket by section
        critical: list[ActionItem] = []
        important: list[ActionItem] = []
        payments: list[ActionItem] = []
        attendance: list[ActionItem] = []
        inactive: list[ActionItem] = []

        for action in actions:
            atype = action.action_type
            pri = action.priority
            if pri == "critical" or atype == "overdue_operational_issue":
                critical.append(action)
            elif atype in {"unpaid_fees_follow_up", "fee_follow_up"}:
                payments.append(action)
            elif atype in {"repeated_absence_intervention"}:
                attendance.append(action)
            elif atype in {"inactivity_reengagement"}:
                inactive.append(action)
            elif pri == "high" or atype in {"workflow_failure_triage", "failed_communication_retry"}:
                important.append(action)
            else:
                important.append(action)

        def _fmt_item(item: ActionItem, index: int) -> str:
            return (
                f"  {index}. [{item.priority.upper()}] {item.subject_id}\n"
                f"     Reason   : {item.reason}\n"
                f"     Next step: {item.suggested_next_step}\n"
                f"     Action ID: {item.action_id}"
            )

        def _section(title: str, items: list[ActionItem]) -> str:
            if not items:
                return ""
            body = "\n".join(_fmt_item(item, i + 1) for i, item in enumerate(items))
            return f"{'=' * 40}\n{title} ({len(items)})\n{'=' * 40}\n{body}"

        header = (
            f"DAILY ACTION LIST — {effective_date.isoformat()}\n"
            f"Tenant: {tenant_id}\n"
            f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
            f"Total items: {len(actions)}"
        )

        sections = [
            _section("CRITICAL", critical),
            _section("IMPORTANT", important),
            _section("PAYMENTS", payments),
            _section("ATTENDANCE", attendance),
            _section("INACTIVE USERS", inactive),
        ]
        body = "\n\n".join(s for s in sections if s)
        if not body:
            body = "No action items for today."

        return f"{header}\n\n{body}"

    # BC-OPS-04 zero-dashboard command vocabulary
    _COMMAND_HELP = (
        "Commands: status | pending | daily | "
        "mark attendance <student_id> <present|absent> | "
        "confirm fee <student_id> | waive fee <student_id> | "
        "send reminder <student_id> | "
        "approve <action_id> | reject <action_id>"
    )

    def execute_message_command(self, *, tenant_id: str, command: str) -> dict[str, Any]:
        """Parse and execute a zero-dashboard message command per BC-OPS-04.

        Supported commands:
        - status                              → summary counts
        - pending                             → list open action IDs + reasons
        - daily                               → return today's Action List document
        - mark attendance <sid> <present|absent>
        - confirm fee <student_id>            → resolve the open fee action for this student
        - waive fee <student_id>              → resolve with waiver note
        - send reminder <student_id>          → create a failed_communication_retry action
        - approve <action_id>                 → resolve action as approved
        - reject <action_id>                  → resolve action as rejected

        CGAP-018 fix: previously no command parsing or reply-action mapping existed.
        """
        parts = command.strip().split()
        if not parts:
            return {"ok": False, "output": self._COMMAND_HELP}

        verb = parts[0].lower()

        # status — summary counts
        if verb == "status":
            open_actions = self.list_open_actions(tenant_id=tenant_id)
            by_priority: dict[str, int] = {}
            for a in open_actions:
                by_priority[a.priority] = by_priority.get(a.priority, 0) + 1
            counts = ", ".join(f"{p}={c}" for p, c in sorted(by_priority.items()))
            return {
                "ok": True,
                "output": f"Open actions: {len(open_actions)} [{counts or 'none'}]",
            }

        # pending — list open actions (abbreviated)
        if verb == "pending":
            open_actions = self.list_open_actions(tenant_id=tenant_id)
            if not open_actions:
                return {"ok": True, "output": "No pending actions."}
            lines = [f"  {a.action_id} | {a.priority} | {a.action_type} | {a.subject_id}" for a in open_actions[:20]]
            suffix = f"\n  ... and {len(open_actions) - 20} more" if len(open_actions) > 20 else ""
            return {"ok": True, "output": "Pending actions:\n" + "\n".join(lines) + suffix}

        # daily — generate and return Action List document
        if verb == "daily":
            doc = self.generate_daily_action_list_document(tenant_id=tenant_id)
            return {"ok": True, "output": doc}

        # mark attendance <student_id> <present|absent>
        if verb == "mark" and len(parts) >= 4 and parts[1].lower() == "attendance":
            student_id = parts[2]
            state = parts[3].lower()
            if state not in {"present", "absent"}:
                return {"ok": False, "output": "State must be 'present' or 'absent'."}
            self._academy_ops_service.upsert_attendance_exception(
                tenant_id=tenant_id,
                run_date=date.today(),
                student_id=student_id,
                attendance_state=state,
                session_ref=f"cmd:{datetime.now(timezone.utc).date().isoformat()}",
            )
            if state == "absent":
                self.create_action_item(
                    tenant_id=tenant_id,
                    action_type="repeated_absence_intervention",
                    priority="medium",
                    subject_type="student",
                    subject_id=student_id,
                    reason="Absence marked via message command.",
                    due_at=datetime.now(timezone.utc) + timedelta(hours=48),
                    suggested_next_step="Verify reason and notify guardian.",
                    metadata={},
                )
            return {"ok": True, "output": f"Attendance marked {state} for {student_id}."}

        # confirm fee <student_id>
        if verb == "confirm" and len(parts) >= 3 and parts[1].lower() == "fee":
            student_id = parts[2]
            resolved = [
                self.resolve_action_item(action_id=a.action_id, resolution_note="Fee confirmed via command.")
                for a in self.list_open_actions(tenant_id=tenant_id)
                if a.action_type in {"unpaid_fees_follow_up", "fee_follow_up"} and a.subject_id == student_id
            ]
            if not resolved:
                return {"ok": False, "output": f"No open fee action found for {student_id}."}
            return {"ok": True, "output": f"Fee action resolved for {student_id} ({len(resolved)} item(s))."}

        # waive fee <student_id>
        if verb == "waive" and len(parts) >= 3 and parts[1].lower() == "fee":
            student_id = parts[2]
            resolved = [
                self.resolve_action_item(action_id=a.action_id, resolution_note="Fee waived via message command.")
                for a in self.list_open_actions(tenant_id=tenant_id)
                if a.action_type in {"unpaid_fees_follow_up", "fee_follow_up"} and a.subject_id == student_id
            ]
            if not resolved:
                return {"ok": False, "output": f"No open fee action found for {student_id}."}
            return {"ok": True, "output": f"Fee waived for {student_id} ({len(resolved)} item(s))."}

        # send reminder <student_id>
        if verb == "send" and len(parts) >= 3 and parts[1].lower() == "reminder":
            student_id = parts[2]
            self.create_action_item(
                tenant_id=tenant_id,
                action_type="failed_communication_retry",
                priority="medium",
                subject_type="student",
                subject_id=student_id,
                reason="Manual reminder requested via command.",
                due_at=datetime.now(timezone.utc) + timedelta(hours=24),
                suggested_next_step="Send reminder via primary channel.",
                metadata={"source": "message_command"},
            )
            return {"ok": True, "output": f"Reminder action created for {student_id}."}

        # approve <action_id>
        if verb == "approve" and len(parts) >= 2:
            action_id = parts[1]
            if action_id not in self._actions:
                return {"ok": False, "output": f"Action {action_id} not found."}
            self.resolve_action_item(action_id=action_id, resolution_note="Approved via message command.")
            return {"ok": True, "output": f"Action {action_id} approved and resolved."}

        # reject <action_id>
        if verb == "reject" and len(parts) >= 2:
            action_id = parts[1]
            if action_id not in self._actions:
                return {"ok": False, "output": f"Action {action_id} not found."}
            self.resolve_action_item(action_id=action_id, resolution_note="Rejected via message command.")
            return {"ok": True, "output": f"Action {action_id} rejected and closed."}

        return {"ok": False, "output": f"Unknown command '{verb}'. {self._COMMAND_HELP}"}

    # ------------------------------------------------------------------ #
    # BC-OPS-01 — Trend/pattern detection                                #
    # ------------------------------------------------------------------ #

    def record_period_snapshot(
        self,
        *,
        tenant_id: str,
        period_key: str,
        signal_counts: dict[str, int],
    ) -> None:
        """Store signal counts for this period so the next period can detect trends.

        Call at end of each operational run with counts from the current period.
        signal_counts keys: "unpaid_fees", "absences", "inactivity", "failed_comms".
        """
        self._period_snapshots[(tenant_id.strip(), period_key)] = dict(signal_counts)

    def detect_operational_patterns(
        self,
        *,
        tenant_id: str,
        current_period_key: str,
        prior_period_key: str,
    ) -> tuple[OperationalPattern, ...]:
        """BC-OPS-01: compare current signals vs stored prior period, return patterns.

        For each signal type where the current count differs significantly from the
        prior period, emits an OperationalPattern with Pattern/Implication/Suggested
        action structure as required by BC-OPS-01 §1.

        Returns an empty tuple if no prior period snapshot is available — caller
        should surface "No prior period data" per BC-ANALYTICS-02 convention.
        """
        prior = self._period_snapshots.get((tenant_id.strip(), prior_period_key))

        run_date = self._active_run_date or date.today()
        self._active_tenant_id = tenant_id.strip()

        # Collect current signal counts
        current: dict[str, int] = {
            "unpaid_fees": len(self.list_unpaid_fee_cases()),
            "absences": len(self.list_absence_cases()),
            "inactivity": len(self.list_inactive_user_cases()),
        }

        # Store current snapshot for next comparison
        self.record_period_snapshot(
            tenant_id=tenant_id,
            period_key=current_period_key,
            signal_counts=current,
        )

        if prior is None:
            return ()

        patterns: list[OperationalPattern] = []

        # --- Unpaid fees trend ---
        prior_fees = prior.get("unpaid_fees", 0)
        curr_fees = current["unpaid_fees"]
        if curr_fees > 0 and prior_fees == 0:
            _p = f"{curr_fees} student(s) now have unpaid fees (up from 0 last period)."
            _i = "New fee overdue cases have appeared since last period — early intervention prevents escalation."
            _s = f"Send fee reminder to all {curr_fees} student(s) with outstanding balances."
            patterns.append(OperationalPattern(
                tenant_id=tenant_id,
                signal_type="fees",
                severity="high",
                pattern=_p,
                implication=_i,
                suggested_action=_s,
                trigger_ref=f"ops://fees/remind_all/{tenant_id}/{run_date.isoformat()}",
                formatted_output=_format_pattern(_p, _i, _s),
            ))
        elif prior_fees > 0 and curr_fees > prior_fees:
            pct = round((curr_fees - prior_fees) / prior_fees * 100, 1)
            _p = f"Unpaid fee cases increased {pct}% this period ({prior_fees} → {curr_fees})."
            _i = "Fee collection rate is declining — revenue at risk if not addressed now."
            _s = f"Send escalation reminder to all {curr_fees} outstanding cases."
            patterns.append(OperationalPattern(
                tenant_id=tenant_id,
                signal_type="fees",
                severity="critical" if pct >= 50 else "high",
                pattern=_p,
                implication=_i,
                suggested_action=_s,
                trigger_ref=f"ops://fees/escalate_all/{tenant_id}/{run_date.isoformat()}",
                formatted_output=_format_pattern(_p, _i, _s),
            ))

        # --- Attendance trend ---
        prior_abs = prior.get("absences", 0)
        curr_abs = current["absences"]
        if curr_abs > prior_abs and prior_abs > 0:
            pct = round((curr_abs - prior_abs) / prior_abs * 100, 1)
            if pct >= 10:
                _p = f"Attendance exceptions increased {pct}% this period ({prior_abs} → {curr_abs})."
                _i = "More students are missing sessions than last period — batch health declining."
                _s = f"Send attendance reminder to {curr_abs} absent student(s)."
                patterns.append(OperationalPattern(
                    tenant_id=tenant_id,
                    signal_type="attendance",
                    severity="high" if pct >= 25 else "medium",
                    pattern=_p,
                    implication=_i,
                    suggested_action=_s,
                    trigger_ref=f"ops://attendance/remind_absent/{tenant_id}/{run_date.isoformat()}",
                    formatted_output=_format_pattern(_p, _i, _s),
                ))
        elif curr_abs > 0 and prior_abs == 0:
            _p = f"{curr_abs} attendance exception(s) detected (none last period)."
            _i = "Attendance issues have appeared — early follow-up prevents dropout."
            _s = f"Contact {curr_abs} absent student(s) today."
            patterns.append(OperationalPattern(
                tenant_id=tenant_id,
                signal_type="attendance",
                severity="medium",
                pattern=_p,
                implication=_i,
                suggested_action=_s,
                trigger_ref=f"ops://attendance/contact_absent/{tenant_id}/{run_date.isoformat()}",
                formatted_output=_format_pattern(_p, _i, _s),
            ))

        # --- Inactivity trend ---
        prior_inact = prior.get("inactivity", 0)
        curr_inact = current["inactivity"]
        if curr_inact > prior_inact and curr_inact > 0:
            new_inactive = curr_inact - prior_inact
            _p = f"{new_inactive} additional student(s) became inactive this period ({prior_inact} → {curr_inact} total)."
            _i = "Student inactivity is growing — unaddressed inactivity is the strongest predictor of dropout."
            _s = f"Send re-engagement message to {curr_inact} inactive student(s)."
            patterns.append(OperationalPattern(
                tenant_id=tenant_id,
                signal_type="inactivity",
                severity="medium",
                pattern=_p,
                implication=_i,
                suggested_action=_s,
                trigger_ref=f"ops://inactivity/reengage_all/{tenant_id}/{run_date.isoformat()}",
                formatted_output=_format_pattern(_p, _i, _s),
            ))

        result = tuple(patterns)
        # BC-OPS-01: auto-push to operator channel when notification_service injected
        if result:
            self.push_patterns_to_operator_channel(patterns=result, tenant_id=tenant_id)
        return result

    # ------------------------------------------------------------------ #
    # BC-OPS-01 — Channel push (CGAP-012)                               #
    # ------------------------------------------------------------------ #

    def push_patterns_to_operator_channel(
        self,
        *,
        patterns: tuple[OperationalPattern, ...],
        tenant_id: str,
    ) -> None:
        """BC-OPS-01: push each pattern's formatted output to the operator's active channel."""
        if not patterns or self._notification_service is None:
            return
        for p in patterns:
            text = p.formatted_output or _format_pattern(p.pattern, p.implication, p.suggested_action)
            try:
                self._notification_service.send(
                    tenant_id=tenant_id,
                    channel="operator",
                    message=text,
                )
            except Exception:
                pass

    # ------------------------------------------------------------------
    # BC-ECON-01: Revenue signal ingestion → Daily Action List — MO-029 / Phase C
    # Revenue risk signals (overdue installments, lapsing subscriptions,
    # churn indicators) are proactively surfaced as CRITICAL/IMPORTANT
    # action items without any operator query.
    # ------------------------------------------------------------------

    def receive_revenue_signal(
        self,
        *,
        tenant_id: str,
        signal_type: str,
        subject_id: str,
        amount: float | None = None,
        currency: str | None = None,
        days_overdue: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ActionItem":
        """Ingest a revenue risk signal and immediately create a Daily Action List item.

        BC-ECON-01: every revenue risk signal must be elevated to operator attention
        without requiring a query. Supported signal types:
          - "installment_overdue"   → CRITICAL if days_overdue >= 14, else IMPORTANT
          - "subscription_lapsing"  → IMPORTANT (renewal due in < 7 days)
          - "churn_risk"            → IMPORTANT
          - "payment_failed"        → IMPORTANT

        Returns the created ActionItem so callers can confirm placement.
        """
        signal_type = signal_type.strip().lower()
        days_over = days_overdue or 0
        amt_str = f" ({currency or ''} {amount:.2f})" if amount is not None else ""

        if signal_type == "installment_overdue":
            priority = "critical" if days_over >= 14 else "high"
            reason = f"Installment overdue by {days_over} day(s){amt_str}."
            next_step = f"Contact {subject_id} to recover overdue payment. Enable auto-reminders to prevent recurrence."
            trigger = f"ops://revenue/follow_up/{tenant_id}/{subject_id}"
        elif signal_type == "subscription_lapsing":
            priority = "high"
            reason = f"Subscription renewal due within {days_over} day(s){amt_str}."
            next_step = f"Send renewal reminder to {subject_id}. Offer payment plan if needed."
            trigger = f"ops://revenue/renewal_reminder/{tenant_id}/{subject_id}"
        elif signal_type == "churn_risk":
            priority = "high"
            reason = f"Churn risk signal detected for {subject_id}."
            next_step = f"Reach out to {subject_id} to understand and address disengagement."
            trigger = f"ops://revenue/churn_outreach/{tenant_id}/{subject_id}"
        elif signal_type == "payment_failed":
            priority = "high"
            reason = f"Payment attempt failed for {subject_id}{amt_str}."
            next_step = f"Contact {subject_id} to arrange alternative payment method."
            trigger = f"ops://revenue/payment_retry/{tenant_id}/{subject_id}"
        else:
            priority = "medium"
            reason = f"Revenue signal [{signal_type}] for {subject_id}{amt_str}."
            next_step = f"Review revenue details for {subject_id}."
            trigger = ""

        return self.create_action_item(
            tenant_id=tenant_id,
            action_type="unpaid_fees_follow_up",
            priority=priority,
            subject_type="student",
            subject_id=subject_id,
            reason=reason,
            due_at=datetime.now(timezone.utc) + timedelta(hours=24 if priority == "critical" else 48),
            suggested_next_step=next_step,
            metadata={
                "signal_type": signal_type,
                "amount": amount,
                "currency": currency,
                "days_overdue": days_overdue,
                "trigger_ref": trigger,
                **(metadata or {}),
            },
        )

    def generate_revenue_action_items(
        self,
        *,
        tenant_id: str,
        revenue_signals: list[dict[str, Any]],
    ) -> list["ActionItem"]:
        """Bulk-ingest revenue signals and return all created action items.

        BC-ECON-01: called by financial_ledger or B3P07 when overdue/lapsing
        events arrive. Each signal dict must contain at minimum:
          {signal_type, subject_id} and optionally {amount, currency, days_overdue}.

        Returns the list of ActionItems added to the Daily Action List.
        """
        created: list[ActionItem] = []
        for signal in revenue_signals:
            item = self.receive_revenue_signal(
                tenant_id=tenant_id,
                signal_type=str(signal.get("signal_type", "unknown")),
                subject_id=str(signal.get("subject_id", "unknown")),
                amount=signal.get("amount"),
                currency=signal.get("currency"),
                days_overdue=signal.get("days_overdue"),
                metadata=signal.get("metadata"),
            )
            created.append(item)
        return created

    # ------------------------------------------------------------------ #
    # BC-OPS-03 — Delivery scheduling (CGAP-016, CGAP-017)              #
    # ------------------------------------------------------------------ #

    def schedule_daily_delivery(
        self,
        *,
        tenant_id: str,
        operator_id: str,
        delivery_hour_utc: int = 8,
    ) -> dict:
        """BC-OPS-03: register a daily 08:00 UTC action-list delivery for this operator."""
        for entry in self._scheduled_deliveries:
            if entry["tenant_id"] == tenant_id and entry["operator_id"] == operator_id:
                entry["delivery_hour_utc"] = delivery_hour_utc
                return {"ok": True, "updated": True}
        self._scheduled_deliveries.append({
            "tenant_id": tenant_id,
            "operator_id": operator_id,
            "delivery_hour_utc": delivery_hour_utc,
        })
        return {"ok": True, "updated": False}

    def run_scheduled_deliveries(self, *, now: datetime | None = None) -> list[dict]:
        """BC-OPS-03: execute any deliveries whose scheduled hour matches the current UTC hour."""
        current = now or datetime.now(timezone.utc)
        results: list[dict] = []
        for entry in self._scheduled_deliveries:
            if current.hour != entry["delivery_hour_utc"]:
                continue
            tenant_id = entry["tenant_id"]
            operator_id = entry["operator_id"]
            self._active_tenant_id = tenant_id
            self._active_run_date = current.date()
            try:
                doc = self.generate_daily_action_list_document(
                    tenant_id=tenant_id,
                    run_date=current.date(),
                )
                result = self.deliver_action_list(
                    tenant_id=tenant_id,
                    document=doc,
                    recipient_id=operator_id,
                )
                results.append({"tenant_id": tenant_id, "operator_id": operator_id, "ok": result.get("ok", False)})
            except Exception as exc:
                results.append({"tenant_id": tenant_id, "operator_id": operator_id, "ok": False, "error": str(exc)})
        return results

    def deliver_action_list(
        self,
        *,
        tenant_id: str,
        document: Any,
        recipient_id: str,
    ) -> dict:
        """BC-OPS-03: deliver a daily action list document to recipient via notification service."""
        if self._notification_service is None:
            return {"ok": False, "reason": "no_notification_service"}
        try:
            self._notification_service.send(
                tenant_id=tenant_id,
                channel="operator",
                recipient_id=recipient_id,
                message=getattr(document, "formatted_summary", str(document)),
            )
            return {"ok": True}
        except Exception as exc:
            return {"ok": False, "reason": str(exc)}

    def has_business_logic_duplication(self) -> bool:
        return False
