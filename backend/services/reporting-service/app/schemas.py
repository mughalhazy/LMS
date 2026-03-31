from __future__ import annotations

from datetime import date
from typing import Dict, Optional

from pydantic import BaseModel, Field

from .models import (
    AnalyticsDashboard,
    ComplianceReport,
    CourseCompletionReport,
    ExportFormat,
    ReportExport,
    ReportType,
)


class ReportFilterRequest(BaseModel):
    tenant_id: str
    department: Optional[str] = None
    manager_id: Optional[str] = None
    course_id: Optional[str] = None
    from_date: Optional[date] = None
    to_date: Optional[date] = None
    workforce_only: bool = False


class DashboardRequest(BaseModel):
    tenant_id: str
    time_granularity: str = Field(default="day")


class ExportReportRequest(BaseModel):
    tenant_id: str
    report_type: ReportType
    report_id: str
    format: ExportFormat
    filters: Dict[str, str] = Field(default_factory=dict)


class ComplianceReportResponse(BaseModel):
    report: ComplianceReport


class CourseCompletionReportResponse(BaseModel):
    report: CourseCompletionReport


class DashboardResponse(BaseModel):
    dashboard: AnalyticsDashboard


class ExportResponse(BaseModel):
    export: ReportExport
