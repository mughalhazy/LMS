from fastapi import FastAPI, Query, Depends
from .security import apply_security_headers, require_jwt

from .schemas import (
    IntegratedRecommendationRequest,
    IntegratedRecommendationResponse,
    BehavioralRecommendationRequest,
    BehavioralRecommendationResponse,
    LearnerRecommendationBundleResponse,
    LearningPathSuggestionRequest,
    LearningPathSuggestionResponse,
    PersonalizedRecommendationRequest,
    PersonalizedRecommendationResponse,
    SkillGapRecommendationRequest,
    SkillGapRecommendationResponse,
    AnalyticsRecommendationRequest,
    LearningInsightRecommendationRequest,
    LearningInsightRecommendationResponse,
)
from .service import RecommendationService

app = FastAPI(title="Recommendation Service", version="1.0.0", dependencies=[Depends(require_jwt)])


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
service = RecommendationService()


@app.post("/api/v1/recommendations/personalized-courses", response_model=PersonalizedRecommendationResponse)
def generate_personalized_course_recommendations(
    request: PersonalizedRecommendationRequest,
) -> PersonalizedRecommendationResponse:
    return PersonalizedRecommendationResponse(items=service.generate_personalized_courses(request))


@app.post("/api/v1/recommendations/skill-gaps", response_model=SkillGapRecommendationResponse)
def generate_skill_gap_recommendations(
    request: SkillGapRecommendationRequest,
) -> SkillGapRecommendationResponse:
    return SkillGapRecommendationResponse(items=service.generate_skill_gap_recommendations(request))


@app.post("/api/v1/recommendations/learning-paths", response_model=LearningPathSuggestionResponse)
def generate_learning_path_suggestions(
    request: LearningPathSuggestionRequest,
) -> LearningPathSuggestionResponse:
    return LearningPathSuggestionResponse(items=service.generate_learning_path_suggestions(request))


@app.post("/api/v1/recommendations/behavioral", response_model=BehavioralRecommendationResponse)
def generate_behavioral_learning_recommendations(
    request: BehavioralRecommendationRequest,
) -> BehavioralRecommendationResponse:
    return BehavioralRecommendationResponse(items=service.generate_behavioral_recommendations(request))


@app.post("/api/v1/recommendations/from-analytics", response_model=BehavioralRecommendationResponse)
def generate_recommendations_from_analytics(
    request: AnalyticsRecommendationRequest,
) -> BehavioralRecommendationResponse:
    return BehavioralRecommendationResponse(items=service.generate_from_analytics(request))


@app.post("/api/v1/recommendations/from-learning-insight", response_model=LearningInsightRecommendationResponse)
def generate_recommendations_from_learning_insight(
    request: LearningInsightRecommendationRequest,
) -> LearningInsightRecommendationResponse:
    return LearningInsightRecommendationResponse(items=service.generate_from_learning_insight(request))


@app.post("/api/v1/recommendations/integrated", response_model=IntegratedRecommendationResponse)
def generate_integrated_recommendations(request: IntegratedRecommendationRequest) -> IntegratedRecommendationResponse:
    courses, learning_paths = service.generate_integrated_recommendations(request)
    return IntegratedRecommendationResponse(personalized_courses=courses, learning_paths=learning_paths)


@app.get("/api/v1/learners/{learner_id}/recommendations", response_model=LearnerRecommendationBundleResponse)
def get_recommendation_bundle(learner_id: str, tenant_id: str = Query(...)) -> LearnerRecommendationBundleResponse:
    return LearnerRecommendationBundleResponse(bundle=service.get_bundle(tenant_id=tenant_id, learner_id=learner_id))

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "recommendation-service"}

@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "recommendation-service", "service_up": 1}
