from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class SourceType(str, Enum):
    PDF = "pdf"
    DOCX = "docx"
    HTML = "html"
    PPT = "ppt"
    TRANSCRIPT = "transcript"
    TEXT = "text"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class SourceDocument(BaseModel):
    document_id: str
    source_type: SourceType
    title: str
    content: str
    language: str = "en"
    metadata: dict[str, str] = Field(default_factory=dict)


class IngestionRules(BaseModel):
    max_chunk_size: int = Field(default=500, ge=100, le=2_000)
    deduplicate: bool = True


class IngestionRequest(BaseModel):
    tenant_id: str
    course_id: str
    documents: list[SourceDocument] = Field(min_length=1)
    course_level: str | None = None
    audience: str | None = None
    language: str = "en"
    rules: IngestionRules = Field(default_factory=IngestionRules)


class TextChunk(BaseModel):
    chunk_id: str
    document_id: str
    heading: str
    text: str
    token_estimate: int


class IngestionResponse(BaseModel):
    ingestion_id: str
    tenant_id: str
    course_id: str
    chunks: list[TextChunk]
    metadata_index: dict[str, str]
    traceability_map: dict[str, str]
    created_at: datetime


class TopicExtractionRequest(BaseModel):
    ingestion_id: str
    course_goals: list[str] = Field(default_factory=list)
    taxonomy_terms: list[str] = Field(default_factory=list)
    top_n_topics: int = Field(default=8, ge=1, le=20)


class Topic(BaseModel):
    topic_id: str
    title: str
    key_concepts: list[str]
    confidence: float
    citations: list[str]
    lesson_order: int


class TopicExtractionResponse(BaseModel):
    extraction_id: str
    ingestion_id: str
    topics: list[Topic]
    prerequisites: dict[str, list[str]]
    created_at: datetime


class LessonGenerationRequest(BaseModel):
    extraction_id: str
    learner_level: DifficultyLevel = DifficultyLevel.BEGINNER
    pacing: str = "standard"
    locale: str = "en-US"


class Lesson(BaseModel):
    lesson_id: str
    topic_id: str
    title: str
    objectives: list[str]
    explanation: str
    worked_example: str
    practice_tasks: list[str]
    summary: str
    estimated_duration_minutes: int


class LessonGenerationResponse(BaseModel):
    generation_id: str
    extraction_id: str
    lessons: list[Lesson]
    created_at: datetime


class QuizGenerationRequest(BaseModel):
    generation_id: str
    questions_per_lesson: int = Field(default=3, ge=1, le=10)


class QuizQuestion(BaseModel):
    question_id: str
    lesson_id: str
    prompt: str
    options: list[str]
    answer: str
    rationale: str
    difficulty: DifficultyLevel


class QuizGenerationResponse(BaseModel):
    quiz_id: str
    generation_id: str
    questions: list[QuizQuestion]
    coverage_percent: float
    estimated_completion_minutes: int
    created_at: datetime


class PipelineRequest(BaseModel):
    ingestion: IngestionRequest
    topic_extraction: TopicExtractionRequest
    lesson_generation: LessonGenerationRequest
    quiz_generation: QuizGenerationRequest


class PipelineResponse(BaseModel):
    ingestion: IngestionResponse
    topic_extraction: TopicExtractionResponse
    lesson_generation: LessonGenerationResponse
    quiz_generation: QuizGenerationResponse
