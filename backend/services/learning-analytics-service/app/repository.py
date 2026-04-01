from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .models import (
    AssessmentAttempt,
    CashflowRecord,
    CourseCompletion,
    CourseEnrollment,
    LearningActivityEvent,
    PathProgressSnapshot,
    RevenueRecord,
)


@dataclass
class AnalyticsRepository:
    enrollments: list[CourseEnrollment] = field(default_factory=list)
    completions: list[CourseCompletion] = field(default_factory=list)
    activities: list[LearningActivityEvent] = field(default_factory=list)
    assessment_attempts: list[AssessmentAttempt] = field(default_factory=list)
    path_snapshots: list[PathProgressSnapshot] = field(default_factory=list)
    revenue_records: list[RevenueRecord] = field(default_factory=list)
    cashflow_records: list[CashflowRecord] = field(default_factory=list)

    @staticmethod
    def _parse_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        raise ValueError("timestamp must be ISO string or datetime")

    @staticmethod
    def _to_int(value: Any, default: int = 0) -> int:
        if value is None:
            return default
        return int(value)

    @staticmethod
    def _to_float(value: Any, default: float = 0.0) -> float:
        if value is None:
            return default
        return float(value)

    def ingest_event(self, event: dict[str, Any]) -> bool:
        event_type = str(event.get("event_type", "")).strip().lower()
        supported_types = {
            "enrollment",
            "completion",
            "activity",
            "assessment_attempt",
            "path_snapshot",
            "revenue",
            "cashflow",
            "commerce_transaction",
            "commerce_refund",
            "commerce_expense",
        }
        if event_type not in supported_types:
            return False

        tenant_id = event.get("tenant_id")
        learner_id = event.get("learner_id")
        course_id = event.get("course_id")
        cohort_id = event.get("cohort_id") or ""
        timestamp_raw = event.get("timestamp") or event.get("event_timestamp")
        try:
            timestamp = self._parse_datetime(timestamp_raw)
        except ValueError:
            return False

        required = [tenant_id]
        if event_type not in {"path_snapshot", "revenue", "cashflow", "commerce_transaction", "commerce_refund", "commerce_expense"}:
            required.append(learner_id)
        if event_type not in {"path_snapshot", "revenue", "cashflow", "commerce_transaction", "commerce_refund", "commerce_expense"}:
            required.append(course_id)
        if any(not value for value in required):
            return False

        if event_type == "enrollment":
            self.enrollments.append(
                CourseEnrollment(
                    tenant_id=tenant_id,
                    learner_id=learner_id,
                    course_id=course_id,
                    cohort_id=cohort_id,
                    enrollment_status=str(event.get("enrollment_status") or "enrolled"),
                    enrolled_at=timestamp,
                )
            )
            return True

        if event_type == "completion":
            self.completions.append(
                CourseCompletion(
                    tenant_id=tenant_id,
                    learner_id=learner_id,
                    course_id=course_id,
                    completion_status=str(event.get("completion_status") or "completed"),
                    completion_timestamp=timestamp,
                    total_time_spent_seconds=self._to_int(event.get("total_time_spent_seconds")),
                )
            )
            return True

        if event_type == "activity":
            self.activities.append(
                LearningActivityEvent(
                    tenant_id=tenant_id,
                    learner_id=learner_id,
                    course_id=course_id,
                    cohort_id=cohort_id,
                    active_minutes=self._to_float(event.get("active_minutes")),
                    content_interactions=self._to_int(event.get("content_interactions")),
                    assessment_attempts=self._to_int(event.get("assessment_attempts")),
                    discussion_actions=self._to_int(event.get("discussion_actions")),
                    event_timestamp=timestamp,
                    sentiment_score=self._to_float(event.get("sentiment_score")),
                )
            )
            return True

        if event_type == "assessment_attempt":
            self.assessment_attempts.append(
                AssessmentAttempt(
                    tenant_id=tenant_id,
                    learner_id=learner_id,
                    course_id=course_id,
                    cohort_id=cohort_id,
                    score=self._to_float(event.get("score")),
                    max_score=max(1.0, self._to_float(event.get("max_score"), default=100.0)),
                    submitted_at=timestamp,
                )
            )
            return True

        if event_type == "path_snapshot":
            learning_path_id = event.get("learning_path_id")
            if not learning_path_id:
                return False
            completed_modules = self._to_int(event.get("completed_modules"))
            total_modules = max(1, self._to_int(event.get("total_modules"), default=1))
            self.path_snapshots.append(
                PathProgressSnapshot(
                    tenant_id=tenant_id,
                    learner_id=learner_id,
                    learning_path_id=learning_path_id,
                    cohort_id=cohort_id,
                    progress_percent=self._to_float(event.get("progress_percent")),
                    completed_modules=completed_modules,
                    total_modules=total_modules,
                    snapshot_timestamp=timestamp,
                )
            )
            return True

        if event_type == "revenue":
            plan_id = str(event.get("plan_id") or event.get("plan_type") or "unknown")
            amount = self._to_float(event.get("amount"))
            if amount < 0:
                return False
            self.revenue_records.append(
                RevenueRecord(
                    tenant_id=tenant_id,
                    owner_id=str(event.get("owner_id") or "unknown"),
                    plan_id=plan_id,
                    amount=amount,
                    billed_at=timestamp,
                    currency=str(event.get("currency") or "USD"),
                    source_event_id=event.get("event_id"),
                    channel=str(event.get("channel") or "direct"),
                )
            )
            return True

        if event_type in {"cashflow", "commerce_transaction", "commerce_refund", "commerce_expense"}:
            owner_id = str(event.get("owner_id") or "unknown")
            currency = str(event.get("currency") or "USD")
            if event_type == "commerce_transaction":
                gross_amount = self._to_float(event.get("amount") or event.get("gross_amount"))
                if gross_amount < 0:
                    return False
                plan_id = str(event.get("plan_id") or event.get("plan_type") or "unknown")
                self.revenue_records.append(
                    RevenueRecord(
                        tenant_id=tenant_id,
                        owner_id=owner_id,
                        plan_id=plan_id,
                        amount=gross_amount,
                        billed_at=timestamp,
                        currency=currency,
                        source_event_id=event.get("event_id"),
                        channel=str(event.get("channel") or "commerce"),
                    )
                )
                settlement_amount = self._to_float(event.get("settlement_amount"), default=gross_amount)
                if settlement_amount < 0:
                    return False
                self.cashflow_records.append(
                    CashflowRecord(
                        tenant_id=tenant_id,
                        owner_id=owner_id,
                        amount=settlement_amount,
                        flow_type="inflow",
                        timestamp=timestamp,
                        currency=currency,
                        category="commerce_settlement",
                        source_event_id=event.get("event_id"),
                    )
                )
                return True

            amount = self._to_float(event.get("amount"))
            if amount < 0:
                return False
            flow_type = str(event.get("flow_type") or "").lower().strip()
            if event_type in {"commerce_refund", "commerce_expense"}:
                flow_type = "outflow"
            if flow_type not in {"inflow", "outflow"}:
                return False
            category = str(event.get("category") or ("commerce_refund" if event_type == "commerce_refund" else "operations"))
            self.cashflow_records.append(
                CashflowRecord(
                    tenant_id=tenant_id,
                    owner_id=owner_id,
                    amount=amount,
                    flow_type=flow_type,
                    timestamp=timestamp,
                    currency=currency,
                    category=category,
                    source_event_id=event.get("event_id"),
                )
            )
            return True

        return False

    def ingest_events(self, events: list[dict[str, Any]]) -> dict[str, int]:
        processed = 0
        rejected = 0
        for event in events:
            if self.ingest_event(event):
                processed += 1
            else:
                rejected += 1
        return {"processed": processed, "rejected": rejected}

    @staticmethod
    def _in_window(timestamp: datetime, start_at: datetime | None, end_at: datetime | None) -> bool:
        if start_at and timestamp < start_at:
            return False
        if end_at and timestamp > end_at:
            return False
        return True

    def list_enrollments(self, tenant_id: str, course_id: str, cohort_id: str | None = None) -> list[CourseEnrollment]:
        return [
            item
            for item in self.enrollments
            if item.tenant_id == tenant_id
            and item.course_id == course_id
            and (cohort_id is None or item.cohort_id == cohort_id)
        ]

    def list_completions(
        self,
        tenant_id: str,
        course_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> list[CourseCompletion]:
        cohort_learners = {
            row.learner_id
            for row in self.enrollments
            if row.tenant_id == tenant_id
            and row.course_id == course_id
            and (cohort_id is None or row.cohort_id == cohort_id)
        }
        return [
            row
            for row in self.completions
            if row.tenant_id == tenant_id
            and row.course_id == course_id
            and row.learner_id in cohort_learners
            and self._in_window(row.completion_timestamp, start_at, end_at)
        ]

    def list_activities(
        self,
        tenant_id: str,
        course_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> list[LearningActivityEvent]:
        return [
            row
            for row in self.activities
            if row.tenant_id == tenant_id
            and row.course_id == course_id
            and (cohort_id is None or row.cohort_id == cohort_id)
            and self._in_window(row.event_timestamp, start_at, end_at)
        ]

    def list_assessment_attempts(
        self,
        tenant_id: str,
        cohort_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> list[AssessmentAttempt]:
        return [
            row
            for row in self.assessment_attempts
            if row.tenant_id == tenant_id
            and row.cohort_id == cohort_id
            and self._in_window(row.submitted_at, start_at, end_at)
        ]

    def list_path_snapshots(
        self,
        tenant_id: str,
        learning_path_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> list[PathProgressSnapshot]:
        return [
            row
            for row in self.path_snapshots
            if row.tenant_id == tenant_id
            and row.learning_path_id == learning_path_id
            and (cohort_id is None or row.cohort_id == cohort_id)
            and self._in_window(row.snapshot_timestamp, start_at, end_at)
        ]

    def list_revenue_records(
        self,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        tenant_id: str | None = None,
        owner_id: str | None = None,
    ) -> list[RevenueRecord]:
        return [
            row
            for row in self.revenue_records
            if (tenant_id is None or row.tenant_id == tenant_id)
            and (owner_id is None or row.owner_id == owner_id)
            and self._in_window(row.billed_at, start_at, end_at)
        ]

    def list_cashflow_records(
        self,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        tenant_id: str | None = None,
        owner_id: str | None = None,
    ) -> list[CashflowRecord]:
        return [
            row
            for row in self.cashflow_records
            if (tenant_id is None or row.tenant_id == tenant_id)
            and (owner_id is None or row.owner_id == owner_id)
            and self._in_window(row.timestamp, start_at, end_at)
        ]
