from __future__ import annotations

from fastapi import FastAPI, Depends
from .security import apply_security_headers, require_jwt

from .schemas import (
    ConceptExplanationRequest,
    ContextualTutoringRequest,
    LearnerQuestionRequest,
    LearningGuidanceRequest,
    TutorResponse,
    TutorSessionSummary,
    AnalyticsTutorRequest,
    LearningInsightTutorRequest,
)
from .service import AITutorService

app = FastAPI(title="AI Tutor Service", version="0.1.0", dependencies=[Depends(require_jwt)])

apply_security_headers(app)
service = AITutorService()


@app.post("/ai-tutor/explanations", response_model=TutorResponse)
def explain_concept(request: ConceptExplanationRequest) -> TutorResponse:
    return service.explain_concept(request)


@app.post("/ai-tutor/questions", response_model=TutorResponse)
def answer_question(request: LearnerQuestionRequest) -> TutorResponse:
    return service.answer_question(request)


@app.post("/ai-tutor/contextual-tutoring", response_model=TutorResponse)
def contextual_tutoring(request: ContextualTutoringRequest) -> TutorResponse:
    return service.provide_contextual_tutoring(request)


@app.post("/ai-tutor/guidance", response_model=TutorResponse)
def learning_guidance(request: LearningGuidanceRequest) -> TutorResponse:
    return service.generate_guidance(request)


@app.post("/ai-tutor/analytics-guidance", response_model=TutorResponse)
def analytics_guidance(request: AnalyticsTutorRequest) -> TutorResponse:
    return service.generate_analytics_guidance(request)


@app.post("/ai-tutor/learning-insight-guidance", response_model=TutorResponse)
def learning_insight_guidance(request: LearningInsightTutorRequest) -> TutorResponse:
    return service.generate_learning_insight_guidance(request)


@app.get("/ai-tutor/sessions/{session_id}", response_model=TutorSessionSummary)
def get_tutor_session(session_id: str, tenant_id: str) -> TutorSessionSummary:
    return service.get_session_summary(tenant_id, session_id)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-tutor-service"}

@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "ai-tutor-service", "service_up": 1}
