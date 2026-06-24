from __future__ import annotations

from datetime import date, datetime, timezone
from enum import Enum
from typing import Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ReportType(str, Enum):
    COMPLIANCE = "compliance"
    COURSE_COMPLETION = "course_completion"
    CERTIFICATION_VALIDITY = "certification_validity"


class ExportFormat(str, Enum):
    CSV = "csv"
    PDF = "pdf"


class CompletionStatus(str, Enum):
    COMPLETED = "completed"
    IN_PROGRESS = "in_progress"
    NOT_STARTED = "not_started"


class ComplianceRecord(BaseModel):
    learner_id: str
    learner_name: str
    department: str
    role: str
    manager_id: str
    policy_id: str
    mandatory_course_id: str
    mandatory_course_title: str
    assignment_date: date
    due_date: date
    completion_status: CompletionStatus
    completion_date: Optional[date] = None
    exemption_flag: bool = False
    exemption_reason: Optional[str] = None
    non_compliance_flag: bool = False
    escalation_level: str = "none"
    reminder_status: str = "none"


class CertificationValidityRecord(BaseModel):
    """B15-033: Certification Validity Report row per compliance-reporting-spec."""
    certification_id: str
    certification_name: str
    issuing_authority: str
    learner_id: str
    learner_name: str
    issued_date: date
    expiry_date: Optional[date]
    validity_status: str  # valid | expired | expiring_soon | revoked
    days_until_expiry: Optional[int] = None
    recertification_required_flag: bool = False
    recertification_due_date: Optional[date] = None
    grace_period_end_date: Optional[date] = None


class CertificationValidityReport(BaseModel):
    envelope: "ReportEnvelope"
    items: List[CertificationValidityRecord]


class CourseCompletionRecord(BaseModel):
    learner_id: str
    learner_name: str
    department: str
    manager_id: str
    course_id: str
    course_title: str
    assignment_type: str
    assigned_at: date
    due_date: date
    completion_status: CompletionStatus
    completion_date: Optional[date] = None
    completion_percentage: float = 0.0
    days_to_complete: Optional[int] = None
    overdue_flag: bool = False


class ReportEnvelope(BaseModel):
    report_id: str = Field(default_factory=lambda: str(uuid4()))
    report_type: ReportType
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: str
    filters: Dict[str, str] = Field(default_factory=dict)
    row_count: int


class ComplianceReport(BaseModel):
    envelope: ReportEnvelope
    items: List[ComplianceRecord]


class CourseCompletionReport(BaseModel):
    envelope: ReportEnvelope
    items: List[CourseCompletionRecord]


class DashboardKPI(BaseModel):
    metric: str
    value: float
    unit: str
    # BC-ANALYTICS-02: every metric must carry a comparative reference
    comparative_context: str = ""  # e.g. "+12% vs last period", "no prior data"


class DashboardTrendPoint(BaseModel):
    label: str
    value: float


class DashboardWidget(BaseModel):
    widget_id: str
    widget_name: str
    metrics: List[DashboardKPI]
    insights: List[str] = Field(default_factory=list)
    trend_points: List[DashboardTrendPoint] = Field(default_factory=list)


class AnalyticsDashboard(BaseModel):
    dashboard_id: str
    tenant_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    time_granularity: str
    widgets: List[DashboardWidget]


class ReportExport(BaseModel):
    export_id: str = Field(default_factory=lambda: str(uuid4()))
    report_id: str
    report_type: ReportType
    format: ExportFormat
    file_name: str
    content_type: str
    data: str
