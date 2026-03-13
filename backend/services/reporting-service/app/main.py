from fastapi import FastAPI, Depends
from .security import apply_security_headers, require_jwt

from .schemas import (
    ComplianceReportResponse,
    CourseCompletionReportResponse,
    DashboardRequest,
    DashboardResponse,
    ExportReportRequest,
    ExportResponse,
    ReportFilterRequest,
)
from .service import ReportingService

app = FastAPI(title="Reporting Service", version="1.0.0", dependencies=[Depends(require_jwt)])

apply_security_headers(app)
service = ReportingService()


@app.post("/reports/compliance", response_model=ComplianceReportResponse)
def generate_compliance_report(request: ReportFilterRequest):
    return ComplianceReportResponse(report=service.generate_compliance_report(request))


@app.post("/reports/course-completion", response_model=CourseCompletionReportResponse)
def generate_course_completion_report(request: ReportFilterRequest):
    return CourseCompletionReportResponse(report=service.generate_course_completion_report(request))


@app.post("/dashboards/analytics", response_model=DashboardResponse)
def generate_analytics_dashboard(request: DashboardRequest):
    return DashboardResponse(dashboard=service.get_analytics_dashboard(request))


@app.post("/exports", response_model=ExportResponse)
def export_report(request: ExportReportRequest):
    return ExportResponse(export=service.export_report(request))
