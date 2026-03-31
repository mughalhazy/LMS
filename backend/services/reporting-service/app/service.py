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
        self._compliance_data = [
            ComplianceRecord(
                learner_id="u-100",
                learner_name="Ava Patel",
                department="Operations",
                role="Supervisor",
                manager_id="mgr-10",
                policy_id="policy-aml",
                mandatory_course_id="course-aml-101",
                mandatory_course_title="AML Foundations",
                assignment_date=date(2026, 1, 3),
                due_date=date(2026, 2, 1),
                completion_status=CompletionStatus.COMPLETED,
                completion_date=date(2026, 1, 20),
                reminder_status="none",
            ),
            ComplianceRecord(
                learner_id="u-101",
                learner_name="Noah Kim",
                department="Operations",
                role="Analyst",
                manager_id="mgr-10",
                policy_id="policy-safety",
                mandatory_course_id="course-safe-201",
                mandatory_course_title="Workplace Safety",
                assignment_date=date(2026, 1, 10),
                due_date=date(2026, 1, 31),
                completion_status=CompletionStatus.IN_PROGRESS,
                non_compliance_flag=True,
                escalation_level="manager",
                reminder_status="scheduled",
            ),
        ]
        self._completion_data = [
            CourseCompletionRecord(
                learner_id="u-100",
                learner_name="Ava Patel",
                department="Operations",
                manager_id="mgr-10",
                course_id="course-aml-101",
                course_title="AML Foundations",
                assignment_type="mandatory",
                assigned_at=date(2026, 1, 3),
                due_date=date(2026, 2, 1),
                completion_status=CompletionStatus.COMPLETED,
                completion_date=date(2026, 1, 20),
                completion_percentage=100,
                days_to_complete=17,
            ),
            CourseCompletionRecord(
                learner_id="u-102",
                learner_name="Liam Chen",
                department="Sales",
                manager_id="mgr-22",
                course_id="course-neg-300",
                course_title="Negotiation Mastery",
                assignment_type="recommended",
                assigned_at=date(2026, 1, 12),
                due_date=date(2026, 2, 20),
                completion_status=CompletionStatus.IN_PROGRESS,
                completion_percentage=48,
                overdue_flag=False,
            ),
        ]

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

    def get_analytics_dashboard(self, req: DashboardRequest) -> AnalyticsDashboard:
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
        widgets = [
            DashboardWidget(
                widget_id="course_completion_monitor",
                widget_name="Course Completion Monitor",
                metrics=[
                    DashboardKPI(metric="completion_rate_percent", value=completion_rate, unit="percent"),
                    DashboardKPI(metric="overdue_completion_count", value=overdue_count, unit="learners"),
                ],
                insights=["Mandatory training completion is healthy, but one learner remains at risk."],
                trend_points=[
                    DashboardTrendPoint(label="week-1", value=42.0),
                    DashboardTrendPoint(label="week-2", value=completion_rate),
                ],
            ),
            DashboardWidget(
                widget_id="sentiment_tracking",
                widget_name="Sentiment Tracking",
                metrics=[
                    DashboardKPI(metric="average_sentiment", value=average_sentiment, unit="score"),
                    DashboardKPI(metric="positive_feedback_share", value=63.0, unit="percent"),
                    DashboardKPI(metric="negative_feedback_share", value=12.0, unit="percent"),
                ],
                insights=["Learner sentiment is positive overall, but negative signals are concentrated in safety training."],
                trend_points=[
                    DashboardTrendPoint(label="week-1", value=0.18),
                    DashboardTrendPoint(label="week-2", value=average_sentiment),
                ],
            ),
            DashboardWidget(
                widget_id="engagement_trends",
                widget_name="Engagement Trends",
                metrics=[
                    DashboardKPI(metric="engagement_delta", value=engagement_delta, unit="score"),
                    DashboardKPI(metric="weekly_active_learners", value=28.0, unit="learners"),
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
                    DashboardKPI(metric="non_compliance_count", value=non_compliant, unit="learners"),
                    DashboardKPI(metric="reminders_pending_count", value=reminder_count, unit="learners"),
                ],
                insights=["Manager visibility is enabled for all mandatory workforce assignments and reminders."],
            ),
        ]
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
