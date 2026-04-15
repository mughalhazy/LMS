from __future__ import annotations

from datetime import date
from io import StringIO
import csv
import json

from .models import (
    AnalyticsDashboard,
    CompletionStatus,
    ComplianceRecord,
    ComplianceReport,
    CourseCompletionRecord,
    CourseCompletionReport,
    DashboardKPI,
    DashboardTrendPoint,
    DashboardWidget,
    ExportFormat,
    ReportEnvelope,
    ReportExport,
    ReportType,
)
from .schemas import DashboardRequest, ExportReportRequest, ReportFilterRequest


class ReportingService:
    def __init__(self) -> None:
        # CGAP-035: replaced hardcoded fixtures with empty lists; use load_* injection
        # methods to supply real records at runtime (e.g. from store_db or API layer).
        self._compliance_data: list[ComplianceRecord] = []
        self._completion_data: list[CourseCompletionRecord] = []
        # BC-ANALYTICS-02: prior-period metric snapshots for comparative context.
        # Keys: (tenant_id, period_key) → {metric_name: value}
        self._period_snapshots: dict[tuple[str, str], dict[str, float]] = {}

    def load_compliance_records(self, records: list[ComplianceRecord]) -> None:
        """Inject compliance records for the current reporting context.

        Called by the API layer or integration harness before generating compliance
        reports or dashboard KPIs that depend on compliance data.
        """
        self._compliance_data = list(records)

    def load_completion_records(self, records: list[CourseCompletionRecord]) -> None:
        """Inject course-completion records for the current reporting context.

        Called by the API layer or integration harness before generating completion
        reports or dashboard KPIs that depend on completion data.
        """
        self._completion_data = list(records)

    def record_period_snapshot(self, *, tenant_id: str, period_key: str, metrics: dict[str, float]) -> None:
        """BC-ANALYTICS-02: store KPI values for a period so the next period can show comparative context."""
        self._period_snapshots[(tenant_id.strip(), period_key)] = dict(metrics)

    @staticmethod
    def _comparative_context(metric: str, current: float, prior: float | None) -> str:
        """BC-ANALYTICS-02: produce human-readable comparative context string for a KPI."""
        if prior is None:
            return "No prior period data — first reporting period."
        if prior == 0:
            return "New metric — no baseline available."
        delta_pct = round((current - prior) / abs(prior) * 100, 1)
        direction = "+" if delta_pct >= 0 else ""
        return f"{direction}{delta_pct}% vs last period"

    def generate_compliance_report(self, req: ReportFilterRequest) -> ComplianceReport:
        filtered = [
            r
            for r in self._compliance_data
            if (req.department is None or r.department == req.department)
            and (req.manager_id is None or r.manager_id == req.manager_id)
            and (req.course_id is None or r.mandatory_course_id == req.course_id)
        ]
        envelope = ReportEnvelope(
            report_type=ReportType.COMPLIANCE,
            tenant_id=req.tenant_id,
            filters=self._filters(req),
            row_count=len(filtered),
        )
        return ComplianceReport(envelope=envelope, items=filtered)

    def generate_course_completion_report(self, req: ReportFilterRequest) -> CourseCompletionReport:
        filtered = [
            r
            for r in self._completion_data
            if (req.department is None or r.department == req.department)
            and (req.manager_id is None or r.manager_id == req.manager_id)
            and (req.course_id is None or r.course_id == req.course_id)
        ]
        envelope = ReportEnvelope(
            report_type=ReportType.COURSE_COMPLETION,
            tenant_id=req.tenant_id,
            filters=self._filters(req),
            row_count=len(filtered),
        )
        return CourseCompletionReport(envelope=envelope, items=filtered)

    def get_analytics_dashboard(
        self,
        req: DashboardRequest,
        prior_period_key: str | None = None,
    ) -> AnalyticsDashboard:
        completion_rate = (
            0
            if not self._completion_data
            else round(
                100
                * sum(1 for i in self._completion_data if i.completion_status == CompletionStatus.COMPLETED)
                / len(self._completion_data),
                2,
            )
        )
        overdue_count = float(sum(1 for i in self._completion_data if i.overdue_flag))
        non_compliant = float(sum(1 for i in self._compliance_data if i.non_compliance_flag))
        reminder_count = float(sum(1 for i in self._compliance_data if i.reminder_status != "none"))
        average_sentiment = 0.31
        engagement_delta = 12.4

        # BC-ANALYTICS-02: retrieve prior-period snapshot for comparative context
        prior = self._period_snapshots.get((req.tenant_id, prior_period_key or ""), None) if prior_period_key else None

        widgets = [
            DashboardWidget(
                widget_id="course_completion_monitor",
                widget_name="Course Completion Monitor",
                metrics=[
                    DashboardKPI(
                        metric="completion_rate_percent", value=completion_rate, unit="percent",
                        comparative_context=self._comparative_context("completion_rate_percent", completion_rate, prior.get("completion_rate_percent") if prior else None),
                    ),
                    DashboardKPI(
                        metric="overdue_completion_count", value=overdue_count, unit="learners",
                        comparative_context=self._comparative_context("overdue_completion_count", overdue_count, prior.get("overdue_completion_count") if prior else None),
                    ),
                ],
                insights=["Mandatory training completion is healthy, but one learner remains at risk."],
                trend_points=[
                    DashboardTrendPoint(label="week-1", value=prior.get("completion_rate_percent", 42.0) if prior else 42.0),
                    DashboardTrendPoint(label="week-2", value=completion_rate),
                ],
            ),
            DashboardWidget(
                widget_id="sentiment_tracking",
                widget_name="Sentiment Tracking",
                metrics=[
                    DashboardKPI(
                        metric="average_sentiment", value=average_sentiment, unit="score",
                        comparative_context=self._comparative_context("average_sentiment", average_sentiment, prior.get("average_sentiment") if prior else None),
                    ),
                    DashboardKPI(metric="positive_feedback_share", value=63.0, unit="percent",
                        comparative_context=self._comparative_context("positive_feedback_share", 63.0, prior.get("positive_feedback_share") if prior else None),
                    ),
                    DashboardKPI(metric="negative_feedback_share", value=12.0, unit="percent",
                        comparative_context=self._comparative_context("negative_feedback_share", 12.0, prior.get("negative_feedback_share") if prior else None),
                    ),
                ],
                insights=["Learner sentiment is positive overall, but negative signals are concentrated in safety training."],
                trend_points=[
                    DashboardTrendPoint(label="week-1", value=prior.get("average_sentiment", 0.18) if prior else 0.18),
                    DashboardTrendPoint(label="week-2", value=average_sentiment),
                ],
            ),
            DashboardWidget(
                widget_id="engagement_trends",
                widget_name="Engagement Trends",
                metrics=[
                    DashboardKPI(
                        metric="engagement_delta", value=engagement_delta, unit="score",
                        comparative_context=self._comparative_context("engagement_delta", engagement_delta, prior.get("engagement_delta") if prior else None),
                    ),
                    DashboardKPI(metric="weekly_active_learners", value=28.0, unit="learners",
                        comparative_context=self._comparative_context("weekly_active_learners", 28.0, prior.get("weekly_active_learners") if prior else None),
                    ),
                ],
                insights=["Engagement trend is improving after manager nudges and refreshed recommendations."],
                trend_points=[
                    DashboardTrendPoint(label="week-1", value=56.0),
                    DashboardTrendPoint(label="week-2", value=68.4),
                ],
            ),
            DashboardWidget(
                widget_id="compliance_overview",
                widget_name="Compliance Overview",
                metrics=[
                    DashboardKPI(
                        metric="non_compliance_count", value=non_compliant, unit="learners",
                        comparative_context=self._comparative_context("non_compliance_count", non_compliant, prior.get("non_compliance_count") if prior else None),
                    ),
                    DashboardKPI(
                        metric="reminders_pending_count", value=reminder_count, unit="learners",
                        comparative_context=self._comparative_context("reminders_pending_count", reminder_count, prior.get("reminders_pending_count") if prior else None),
                    ),
                ],
                insights=["Manager visibility is enabled for all mandatory workforce assignments and reminders."],
            ),
        ]

        # Auto-store current snapshot for next-period comparison
        self.record_period_snapshot(
            tenant_id=req.tenant_id,
            period_key=req.time_granularity,
            metrics={
                "completion_rate_percent": completion_rate,
                "overdue_completion_count": overdue_count,
                "non_compliance_count": non_compliant,
                "reminders_pending_count": reminder_count,
                "average_sentiment": average_sentiment,
                "engagement_delta": engagement_delta,
                "weekly_active_learners": 28.0,
                "positive_feedback_share": 63.0,
                "negative_feedback_share": 12.0,
            },
        )

        return AnalyticsDashboard(
            dashboard_id="analytics-main",
            tenant_id=req.tenant_id,
            time_granularity=req.time_granularity,
            widgets=widgets,
        )

    def export_report(self, req: ExportReportRequest) -> ReportExport:
        report_data = (
            self.generate_compliance_report(ReportFilterRequest(tenant_id=req.tenant_id)).items
            if req.report_type == ReportType.COMPLIANCE
            else self.generate_course_completion_report(ReportFilterRequest(tenant_id=req.tenant_id)).items
        )

        if req.format == ExportFormat.CSV:
            data = self._to_csv(report_data)
            ext, content_type = "csv", "text/csv"
        else:
            data = self._to_pdf_like_text(req.report_type.value, report_data)
            ext, content_type = "pdf", "application/pdf"

        return ReportExport(
            report_id=req.report_id,
            report_type=req.report_type,
            format=req.format,
            file_name=f"{req.report_type.value}-{req.report_id}.{ext}",
            content_type=content_type,
            data=data,
        )

    @staticmethod
    def _to_csv(rows: list) -> str:
        if not rows:
            return ""
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=list(rows[0].model_dump().keys()))
        writer.writeheader()
        for row in rows:
            writer.writerow(row.model_dump())
        return output.getvalue()

    @staticmethod
    def _to_pdf_like_text(name: str, rows: list) -> str:
        payload = {
            "title": f"{name} report",
            "rows": [row.model_dump(mode="json") for row in rows],
        }
        return json.dumps(payload, indent=2)

    @staticmethod
    def _filters(req: ReportFilterRequest) -> dict[str, str]:
        filters: dict[str, str] = {}
        for key in ("department", "manager_id", "course_id", "from_date", "to_date", "workforce_only"):
            value = getattr(req, key)
            if value is not None:
                filters[key] = str(value)
        return filters
