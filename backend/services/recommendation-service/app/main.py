from fastapi import FastAPI, Query, Depends
from .security import apply_security_headers, require_jwt

from .schemas import (
    BehavioralRecommendationRequest,
    BehavioralRecommendationResponse,
    LearnerRecommendationBundleResponse,
    LearningPathSuggestionRequest,
    LearningPathSuggestionResponse,
    PersonalizedRecommendationRequest,
    PersonalizedRecommendationResponse,
    SkillGapRecommendationRequest,
    SkillGapRecommendationResponse,
)
from .service import RecommendationService

app = FastAPI(title="Recommendation Service", version="1.0.0", dependencies=[Depends(require_jwt)])

apply_security_headers(app)
service = RecommendationService()


@app.post("/recommendations/personalized-courses", response_model=PersonalizedRecommendationResponse)
def generate_personalized_course_recommendations(
    request: PersonalizedRecommendationRequest,
) -> PersonalizedRecommendationResponse:
    return PersonalizedRecommendationResponse(items=service.generate_personalized_courses(request))


@app.post("/recommendations/skill-gaps", response_model=SkillGapRecommendationResponse)
def generate_skill_gap_recommendations(
    request: SkillGapRecommendationRequest,
) -> SkillGapRecommendationResponse:
    return SkillGapRecommendationResponse(items=service.generate_skill_gap_recommendations(request))


@app.post("/recommendations/learning-paths", response_model=LearningPathSuggestionResponse)
def generate_learning_path_suggestions(
    request: LearningPathSuggestionRequest,
) -> LearningPathSuggestionResponse:
    return LearningPathSuggestionResponse(items=service.generate_learning_path_suggestions(request))


@app.post("/recommendations/behavioral", response_model=BehavioralRecommendationResponse)
def generate_behavioral_learning_recommendations(
    request: BehavioralRecommendationRequest,
) -> BehavioralRecommendationResponse:
    return BehavioralRecommendationResponse(items=service.generate_behavioral_recommendations(request))


@app.get("/learners/{learner_id}/recommendations", response_model=LearnerRecommendationBundleResponse)
def get_recommendation_bundle(learner_id: str, tenant_id: str = Query(...)) -> LearnerRecommendationBundleResponse:
    return LearnerRecommendationBundleResponse(bundle=service.get_bundle(tenant_id=tenant_id, learner_id=learner_id))

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "recommendation-service"}

@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "recommendation-service", "service_up": 1}

