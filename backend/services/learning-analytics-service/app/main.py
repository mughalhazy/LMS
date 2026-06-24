"""FastAPI REST layer for learning-analytics-service.

Routes anchored to api_endpoints.yaml; additional methods from LearningAnalyticsAPI
cover economics, AI signals, risk insights, and network effects.
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, List

from fastapi import Depends, FastAPI, Header, HTTPException, Query

from .repository import AnalyticsRepository
from .schemas import CourseAnalyticsQuery, LearningPathAnalyticsQuery, TimeWindowQuery
from .security import apply_security_headers, require_jwt
from .service import LearningAnalyticsService


class LearningAnalyticsAPI:
    def __init__(self, repository: AnalyticsRepository | None = None) -> None:
        self.service = LearningAnalyticsService(repository or AnalyticsRepository())

    def get_course_completion_analytics(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.course_completion_analytics(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_learner_engagement_metrics(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.learner_engagement_metrics(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_engagement_trends(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.engagement_trends(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_engagement_dashboard(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.engagement_dashboard(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_cohort_performance_metrics(self, cohort_id: str, query: TimeWindowQuery) -> dict:
        return self.service.cohort_performance_metrics(
            tenant_id=query.tenant_id,
            cohort_id=cohort_id,
            start_at=query.start_at,
            end_at=query.end_at,
        )

    def get_learning_path_completion_analysis(self, learning_path_id: str, query: LearningPathAnalyticsQuery) -> dict:
        return self.service.learning_path_completion_analysis(
            tenant_id=query.tenant_id,
            learning_path_id=learning_path_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def ingest_events(self, events: list[dict[str, Any]]) -> dict:
        return self.service.ingest_events(events)

    def get_learning_and_performance_metrics(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.learning_and_performance_metrics(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_revenue_metrics(self, query: TimeWindowQuery) -> dict:
        return self.service.revenue_metrics(
            start_at=query.start_at,
            end_at=query.end_at,
            tenant_id=query.tenant_id,
            owner_id=query.owner_id,
        )

    def get_cashflow_metrics(self, query: TimeWindowQuery) -> dict:
        return self.service.cashflow_metrics(
            start_at=query.start_at,
            end_at=query.end_at,
            tenant_id=query.tenant_id,
            owner_id=query.owner_id,
        )

    def get_profitability_metrics(self, query: TimeWindowQuery) -> dict:
        return self.service.profitability_metrics(
            start_at=query.start_at,
            end_at=query.end_at,
            tenant_id=query.tenant_id,
            owner_id=query.owner_id,
        )

    def get_owner_economics(self, query: TimeWindowQuery) -> dict:
        return {
            "revenue": self.get_revenue_metrics(query),
            "cashflow": self.get_cashflow_metrics(query),
            "profitability": self.get_profitability_metrics(query),
        }

    def get_ai_service_signals(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.ai_service_signals(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_learner_risk_insights(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.learner_risk_insights(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )

    def get_network_effect_insights(self, course_id: str, query: CourseAnalyticsQuery) -> dict:
        return self.service.network_effect_insights(
            tenant_id=query.tenant_id,
            course_id=course_id,
            start_at=query.start_at,
            end_at=query.end_at,
            cohort_id=query.cohort_id,
        )


# ── FastAPI app ───────────────────────────────────────────────────────────────

_api = LearningAnalyticsAPI()
# B06-002: multi-tenant-isolation-model §2 — JWT required
app = FastAPI(title="learning-analytics-service", version="1.0.0", dependencies=[Depends(require_jwt)])


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


def _require_tenant(
    x_tenant_id: Annotated[str | None, Header()] = None,
) -> str:
    if not x_tenant_id:
        raise HTTPException(status_code=400, detail="missing_tenant_id")
    return x_tenant_id


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"invalid datetime: {value!r}") from exc


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "learning-analytics-service"}


@app.get("/metrics")
def metrics() -> dict:
    return {"service": "learning-analytics-service", "service_up": 1}


@app.post("/api/v1/analytics/events")
def ingest_events(events: List[dict]) -> dict:
    return _api.ingest_events(events)


# ── Course analytics (api_endpoints.yaml) ────────────────────────────────────

@app.get("/api/v1/analytics/courses/{course_id}/completion")
def course_completion(
    course_id: str,
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    cohort_id: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = CourseAnalyticsQuery(tenant_id=tenant_id, start_at=_dt(start_at), end_at=_dt(end_at), cohort_id=cohort_id)
    return _api.get_course_completion_analytics(course_id, query)


@app.get("/api/v1/analytics/courses/{course_id}/engagement")
def learner_engagement(
    course_id: str,
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    cohort_id: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = CourseAnalyticsQuery(tenant_id=tenant_id, start_at=_dt(start_at), end_at=_dt(end_at), cohort_id=cohort_id)
    return _api.get_learner_engagement_metrics(course_id, query)


@app.get("/api/v1/analytics/courses/{course_id}/engagement/trends")
def engagement_trends(
    course_id: str,
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    cohort_id: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = CourseAnalyticsQuery(tenant_id=tenant_id, start_at=_dt(start_at), end_at=_dt(end_at), cohort_id=cohort_id)
    return _api.get_engagement_trends(course_id, query)


@app.get("/api/v1/analytics/courses/{course_id}/engagement/dashboard")
def engagement_dashboard(
    course_id: str,
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    cohort_id: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = CourseAnalyticsQuery(tenant_id=tenant_id, start_at=_dt(start_at), end_at=_dt(end_at), cohort_id=cohort_id)
    return _api.get_engagement_dashboard(course_id, query)


@app.get("/api/v1/analytics/courses/{course_id}/performance")
def learning_performance(
    course_id: str,
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    cohort_id: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = CourseAnalyticsQuery(tenant_id=tenant_id, start_at=_dt(start_at), end_at=_dt(end_at), cohort_id=cohort_id)
    return _api.get_learning_and_performance_metrics(course_id, query)


@app.get("/api/v1/analytics/courses/{course_id}/ai-signals")
def ai_signals(
    course_id: str,
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    cohort_id: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = CourseAnalyticsQuery(tenant_id=tenant_id, start_at=_dt(start_at), end_at=_dt(end_at), cohort_id=cohort_id)
    return _api.get_ai_service_signals(course_id, query)


@app.get("/api/v1/analytics/courses/{course_id}/risk-insights")
def risk_insights(
    course_id: str,
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    cohort_id: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = CourseAnalyticsQuery(tenant_id=tenant_id, start_at=_dt(start_at), end_at=_dt(end_at), cohort_id=cohort_id)
    return _api.get_learner_risk_insights(course_id, query)


@app.get("/api/v1/analytics/courses/{course_id}/network-effects")
def network_effects(
    course_id: str,
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    cohort_id: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = CourseAnalyticsQuery(tenant_id=tenant_id, start_at=_dt(start_at), end_at=_dt(end_at), cohort_id=cohort_id)
    return _api.get_network_effect_insights(course_id, query)


# ── Cohort and learning-path analytics (api_endpoints.yaml) ──────────────────

@app.get("/api/v1/analytics/cohorts/{cohort_id}/performance")
def cohort_performance(
    cohort_id: str,
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = TimeWindowQuery(tenant_id=tenant_id, start_at=_dt(start_at), end_at=_dt(end_at))
    return _api.get_cohort_performance_metrics(cohort_id, query)


@app.get("/api/v1/analytics/learning-paths/{learning_path_id}/completion")
def path_completion(
    learning_path_id: str,
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    cohort_id: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = LearningPathAnalyticsQuery(
        tenant_id=tenant_id, start_at=_dt(start_at), end_at=_dt(end_at), cohort_id=cohort_id
    )
    return _api.get_learning_path_completion_analysis(learning_path_id, query)


# ── Owner economics ───────────────────────────────────────────────────────────

@app.get("/api/v1/analytics/economics/revenue")
def revenue(
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    owner_id: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = TimeWindowQuery(tenant_id=tenant_id, owner_id=owner_id, start_at=_dt(start_at), end_at=_dt(end_at))
    return _api.get_revenue_metrics(query)


@app.get("/api/v1/analytics/economics/cashflow")
def cashflow(
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    owner_id: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = TimeWindowQuery(tenant_id=tenant_id, owner_id=owner_id, start_at=_dt(start_at), end_at=_dt(end_at))
    return _api.get_cashflow_metrics(query)


@app.get("/api/v1/analytics/economics/profitability")
def profitability(
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    owner_id: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = TimeWindowQuery(tenant_id=tenant_id, owner_id=owner_id, start_at=_dt(start_at), end_at=_dt(end_at))
    return _api.get_profitability_metrics(query)


@app.get("/api/v1/analytics/economics")
def owner_economics(
    start_at: str | None = Query(default=None),
    end_at: str | None = Query(default=None),
    owner_id: str | None = Query(default=None),
    tenant_id: str = Depends(_require_tenant),
) -> dict:
    query = TimeWindowQuery(tenant_id=tenant_id, owner_id=owner_id, start_at=_dt(start_at), end_at=_dt(end_at))
    return _api.get_owner_economics(query)
