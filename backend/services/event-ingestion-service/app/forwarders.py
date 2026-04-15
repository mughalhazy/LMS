from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List

from .models import EventFamily, ForwardResult, NormalizedEvent


class EventForwarder(ABC):
    @property
    @abstractmethod
    def target(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def should_forward(self, event: NormalizedEvent) -> bool:
        raise NotImplementedError

    @abstractmethod
    def forward(self, event: NormalizedEvent) -> ForwardResult:
        raise NotImplementedError


class AnalyticsForwarder(EventForwarder):
    @property
    def target(self) -> str:
        return "analytics"

    def should_forward(self, event: NormalizedEvent) -> bool:
        return True

    def forward(self, event: NormalizedEvent) -> ForwardResult:
        return ForwardResult(target=self.target, accepted=True)


class AIForwarder(EventForwarder):
    _eligible = {
        EventFamily.USER,
        EventFamily.COURSE,
        EventFamily.LESSON,
        EventFamily.PROGRESS,
        EventFamily.ASSESSMENT,
        EventFamily.CERTIFICATE,
        EventFamily.AI,
    }

    @property
    def target(self) -> str:
        return "ai"

    def should_forward(self, event: NormalizedEvent) -> bool:
        return event.family in self._eligible

    def forward(self, event: NormalizedEvent) -> ForwardResult:
        if not self.should_forward(event):
            return ForwardResult(target=self.target, accepted=False, reason="family_not_enabled")
        return ForwardResult(target=self.target, accepted=True)


# ─── CGAP-019: WorkflowForwarder ──────────────────────────────────────────────
# Previously events were ingested but never reached the workflow engine, breaking
# the entire event-driven automation chain (BC-WF-01, BC-OPS-01).
# References: workflow_engine_spec.md BC-WF-01, ARCH_05, event_ingestion_spec.md §7

_WORKFLOW_ELIGIBLE_FAMILIES = {
    EventFamily.ENROLLMENT,
    EventFamily.ASSESSMENT,
    EventFamily.PROGRESS,
    EventFamily.COURSE,
    EventFamily.USER,
    EventFamily.FEE,
    EventFamily.ATTENDANCE,
    EventFamily.OPERATIONS,
}


class WorkflowForwarder(EventForwarder):
    """Forward domain events to the workflow engine for automation rule matching.

    Accepts any event from a workflow-eligible family and calls
    WorkflowEngine.handle_event_envelope() with the canonical envelope dict.
    Rule matching inside the workflow engine determines which (if any) workflow fires.

    The workflow_handler must implement handle_event_envelope(dict) -> dict.
    """

    def __init__(self, workflow_handler: Any) -> None:
        self._handler = workflow_handler

    @property
    def target(self) -> str:
        return "workflow-engine"

    def should_forward(self, event: NormalizedEvent) -> bool:
        return event.family in _WORKFLOW_ELIGIBLE_FAMILIES

    def forward(self, event: NormalizedEvent) -> ForwardResult:
        if not self.should_forward(event):
            return ForwardResult(target=self.target, accepted=False, reason="family_not_workflow_eligible")
        envelope = _to_canonical_envelope_dict(event)
        try:
            self._handler.handle_event_envelope(envelope)
            return ForwardResult(target=self.target, accepted=True)
        except Exception as exc:
            return ForwardResult(target=self.target, accepted=False, reason=f"workflow_handler_error:{exc}")


# ─── CGAP-020: OperationsOSForwarder ──────────────────────────────────────────
# Previously operational events (fee.overdue, attendance.marked, user_inactive)
# were never routed to operations-os for proactive pattern detection (BC-OPS-01).
# References: operations_os_spec.md BC-OPS-01, BC-OPS-02

_OPERATIONS_ELIGIBLE_FAMILIES = {
    EventFamily.FEE,
    EventFamily.ATTENDANCE,
    EventFamily.USER,
    EventFamily.OPERATIONS,
}

_OPERATIONS_ELIGIBLE_EVENT_TYPES = {
    "fee.overdue",
    "fee.due",
    "payment.missed",
    "payment.overdue",
    "attendance.marked",
    "user_inactive",
    "learner.inactivity_threshold_crossed",
    "communication.failed",
    "operations.issue_overdue",
}


class OperationsOSForwarder(EventForwarder):
    """Forward operational events to operations-os for proactive pattern detection.

    Filters on family + a curated set of operational event types, then calls
    OperationsOSService.receive_operational_event() with the canonical envelope dict.

    The ops_handler must implement receive_operational_event(dict) -> None.
    """

    def __init__(self, ops_handler: Any) -> None:
        self._handler = ops_handler

    @property
    def target(self) -> str:
        return "operations-os"

    def should_forward(self, event: NormalizedEvent) -> bool:
        return (
            event.family in _OPERATIONS_ELIGIBLE_FAMILIES
            or event.event_type in _OPERATIONS_ELIGIBLE_EVENT_TYPES
        )

    def forward(self, event: NormalizedEvent) -> ForwardResult:
        if not self.should_forward(event):
            return ForwardResult(target=self.target, accepted=False, reason="event_not_operations_eligible")
        envelope = _to_canonical_envelope_dict(event)
        try:
            self._handler.receive_operational_event(envelope)
            return ForwardResult(target=self.target, accepted=True)
        except Exception as exc:
            return ForwardResult(target=self.target, accepted=False, reason=f"ops_handler_error:{exc}")


# ─── Shared helper ────────────────────────────────────────────────────────────

def _to_canonical_envelope_dict(event: NormalizedEvent) -> dict[str, Any]:
    """Convert NormalizedEvent to canonical event envelope dict.

    Output conforms to docs/anchors/event_envelope.md (7-field schema):
    event_id, event_type, timestamp, tenant_id, correlation_id, payload, metadata.
    """
    metadata: dict[str, Any] = {
        "schema_version": "v1",
        "producer": {"service": event.source, "domain": event.family.value},
        "trace_id": event.trace.trace_id,
    }
    if event.trace.causation_id:
        metadata["causation_id"] = event.trace.causation_id
    if event.actor:
        metadata["actor"] = {
            "user_id": event.actor.actor_id,
            "role": event.actor.actor_type,
        }
    if event.entity:
        metadata["entity"] = {
            "type": event.entity.entity_type,
            "id": event.entity.entity_id,
        }
    return {
        "event_id": event.event_id,
        "event_type": event.event_type,
        "timestamp": event.timestamp.isoformat(),
        "tenant_id": event.tenant_id,
        "correlation_id": event.trace.correlation_id,
        "payload": event.payload,
        "metadata": metadata,
    }


# ─── MO-035 / Phase D: RevenueSignalForwarder ─────────────────────────────────
# BC-ECON-01: revenue risk events from B3P07 / financial_ledger must be
# automatically forwarded to OperationsOSService.generate_revenue_action_items()
# so that overdue installments and revenue anomalies appear in the Daily Action
# List without any operator query.
# Depends on: MO-029 (receive_revenue_signal in operations-os).
# Without this forwarder the MO-029 methods exist but are never called from
# the event bus — the revenue → DAL chain is broken.

_REVENUE_SIGNAL_EVENT_TYPES: dict[str, str] = {
    # event_type → revenue signal_type for receive_revenue_signal()
    "academy.installment.overdue": "installment_overdue",
    "payment.installment.overdue": "installment_overdue",
    "fee.installment.overdue": "installment_overdue",
    "subscription.lapsing": "subscription_lapsing",
    "subscription.renewal_due": "subscription_lapsing",
    "revenue.churn_risk": "churn_risk",
    "payment.failed": "payment_failed",
    "payment.capture.failed": "payment_failed",
}


class RevenueSignalForwarder(EventForwarder):
    """Forward revenue risk events to operations-os Daily Action List (BC-ECON-01 / MO-035).

    Maps canonical event types from B3P07 / financial_ledger to the signal
    vocabulary expected by OperationsOSService.receive_revenue_signal().
    The ops_handler must implement receive_revenue_signal(**kwargs) -> ActionItem.
    """

    def __init__(self, ops_handler: Any) -> None:
        self._handler = ops_handler

    @property
    def target(self) -> str:
        return "operations-os/revenue"

    def should_forward(self, event: NormalizedEvent) -> bool:
        return event.event_type in _REVENUE_SIGNAL_EVENT_TYPES

    def forward(self, event: NormalizedEvent) -> ForwardResult:
        if not self.should_forward(event):
            return ForwardResult(target=self.target, accepted=False, reason="event_not_revenue_signal")

        signal_type = _REVENUE_SIGNAL_EVENT_TYPES[event.event_type]
        payload = event.payload or {}

        try:
            self._handler.receive_revenue_signal(
                tenant_id=event.tenant_id,
                signal_type=signal_type,
                subject_id=str(
                    payload.get("student_id")
                    or payload.get("user_id")
                    or payload.get("entity_id")
                    or (event.entity.entity_id if event.entity else "unknown")
                ),
                amount=payload.get("amount") or payload.get("installment_amount"),
                currency=payload.get("currency"),
                days_overdue=payload.get("days_overdue") or payload.get("overdue_days"),
                metadata={"source_event_type": event.event_type, "event_id": event.event_id},
            )
            return ForwardResult(target=self.target, accepted=True)
        except Exception as exc:
            return ForwardResult(
                target=self.target,
                accepted=False,
                reason=f"revenue_signal_handler_error:{exc}",
            )


# ─── Pipeline ─────────────────────────────────────────────────────────────────

class ForwardingPipeline:
    def __init__(self, forwarders: List[EventForwarder]):
        self._forwarders = forwarders

    def publish(self, event: NormalizedEvent) -> List[ForwardResult]:
        return [forwarder.forward(event) for forwarder in self._forwarders]

    def health(self) -> bool:
        return True
