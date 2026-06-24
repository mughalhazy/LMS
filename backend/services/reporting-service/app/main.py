from fastapi import FastAPI, Depends
from .security import apply_security_headers, require_jwt

from .schemas import (
    CertificationValidityReportResponse,
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


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


# FA-024 / G-24: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()


apply_security_headers(app)
service = ReportingService()


@app.post("/api/v1/reports/compliance", response_model=ComplianceReportResponse)
def generate_compliance_report(request: ReportFilterRequest):
    return ComplianceReportResponse(report=service.generate_compliance_report(request))


@app.post("/api/v1/reports/certification-validity", response_model=CertificationValidityReportResponse)
def generate_certification_validity_report(request: ReportFilterRequest):
    """B15-033: Certification Validity Report."""
    return CertificationValidityReportResponse(
        report=service.generate_certification_validity_report(request)
    )


@app.post("/api/v1/reports/course-completion", response_model=CourseCompletionReportResponse)
def generate_course_completion_report(request: ReportFilterRequest):
    return CourseCompletionReportResponse(report=service.generate_course_completion_report(request))


@app.post("/api/v1/dashboards/analytics", response_model=DashboardResponse)
def generate_analytics_dashboard(request: DashboardRequest):
    return DashboardResponse(dashboard=service.get_analytics_dashboard(request))


@app.post("/api/v1/exports", response_model=ExportResponse)
def export_report(request: ExportReportRequest):
    return ExportResponse(export=service.export_report(request))


# B06-005: analytics-api.md defines POST /api/v1/analytics/compliance/reports — alias
app.add_api_route(
    "/api/v1/analytics/compliance/reports",
    generate_compliance_report,
    methods=["POST"],
    response_model=ComplianceReportResponse,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "reporting-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "reporting-service", "service_up": 1}
