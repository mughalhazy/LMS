from __future__ import annotations

from fastapi import FastAPI, Depends
from .security import apply_security_headers, require_jwt

from .schemas import (
    IngestionRequest,
    IngestionResponse,
    LessonGenerationRequest,
    LessonGenerationResponse,
    PipelineRequest,
    PipelineResponse,
    QuizGenerationRequest,
    QuizGenerationResponse,
    TopicExtractionRequest,
    TopicExtractionResponse,
)
from .service import CourseGenerationService

app = FastAPI(title="Course Generation Service", version="0.1.0", dependencies=[Depends(require_jwt)])

apply_security_headers(app)
service = CourseGenerationService()


@app.post("/course-generation/ingestions", response_model=IngestionResponse)
def ingest_documents(request: IngestionRequest) -> IngestionResponse:
    return service.ingest_documents(request)


@app.post("/course-generation/topics:extract", response_model=TopicExtractionResponse)
def extract_topics(request: TopicExtractionRequest) -> TopicExtractionResponse:
    return service.extract_topics(request)


@app.post("/course-generation/lessons:generate", response_model=LessonGenerationResponse)
def generate_lessons(request: LessonGenerationRequest) -> LessonGenerationResponse:
    return service.generate_lessons(request)


@app.post("/course-generation/quizzes:generate", response_model=QuizGenerationResponse)
def generate_quizzes(request: QuizGenerationRequest) -> QuizGenerationResponse:
    return service.generate_quizzes(request)


@app.post("/course-generation/pipeline:run", response_model=PipelineResponse)
def run_pipeline(request: PipelineRequest) -> PipelineResponse:
    return service.run_pipeline(request)

@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "course-generation-service"}

@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "course-generation-service", "service_up": 1}

