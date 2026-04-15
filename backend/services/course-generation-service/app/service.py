from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from .llm_client import LLMClient
from .schemas import (
    DifficultyLevel,
    IngestionRequest,
    IngestionResponse,
    Lesson,
    LessonGenerationRequest,
    LessonGenerationResponse,
    PipelineRequest,
    PipelineResponse,
    QuizGenerationRequest,
    QuizGenerationResponse,
    QuizQuestion,
    TextChunk,
    Topic,
    TopicExtractionRequest,
    TopicExtractionResponse,
)

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "from",
    "this",
    "into",
    "your",
    "have",
    "about",
    "will",
    "you",
    "are",
}

# Maximum characters of chunk text sent to the LLM in a single request
_LLM_CONTEXT_CHAR_LIMIT = 8_000


@dataclass
class PipelineContext:
    ingestion: IngestionResponse
    topics: TopicExtractionResponse | None = None
    lessons: LessonGenerationResponse | None = None


class CourseGenerationService:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self._llm_client = llm_client
        self._ingestions: dict[str, IngestionResponse] = {}
        self._topic_extractions: dict[str, TopicExtractionResponse] = {}
        self._lesson_generations: dict[str, LessonGenerationResponse] = {}

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def ingest_documents(self, request: IngestionRequest) -> IngestionResponse:
        ingestion_id = f"ing-{uuid4()}"
        chunks: list[TextChunk] = []
        traceability_map: dict[str, str] = {}
        seen_payloads: set[str] = set()

        for document in request.documents:
            for idx, paragraph in enumerate(self._chunk_content(document.content, request.rules.max_chunk_size), start=1):
                normalized = paragraph.strip().lower()
                if request.rules.deduplicate and normalized in seen_payloads:
                    continue
                seen_payloads.add(normalized)

                chunk_id = f"{document.document_id}-c{idx}"
                heading = f"{document.title} section {idx}"
                chunk = TextChunk(
                    chunk_id=chunk_id,
                    document_id=document.document_id,
                    heading=heading,
                    text=paragraph.strip(),
                    token_estimate=len(paragraph.split()),
                )
                chunks.append(chunk)
                traceability_map[chunk_id] = document.document_id

        metadata_index = {
            "course_level": request.course_level or "unspecified",
            "audience": request.audience or "unspecified",
            "language": request.language,
            "document_count": str(len(request.documents)),
            "chunk_count": str(len(chunks)),
        }

        response = IngestionResponse(
            ingestion_id=ingestion_id,
            tenant_id=request.tenant_id,
            course_id=request.course_id,
            chunks=chunks,
            metadata_index=metadata_index,
            traceability_map=traceability_map,
            created_at=self._now(),
        )
        self._ingestions[ingestion_id] = response
        return response

    def extract_topics(self, request: TopicExtractionRequest) -> TopicExtractionResponse:
        ingestion = self._ingestions.get(request.ingestion_id)
        if not ingestion:
            raise HTTPException(status_code=404, detail="Ingestion not found")

        # LLM path — falls through to word-frequency on failure or absent client
        if self._llm_client is not None:
            llm_result = self._extract_topics_llm(request, ingestion)
            if llm_result is not None:
                return llm_result

        token_counter = Counter()
        citations: dict[str, list[str]] = {}

        for chunk in ingestion.chunks:
            words = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", chunk.text.lower())
            for word in words:
                if word in STOPWORDS:
                    continue
                token_counter[word] += 1
                citations.setdefault(word, [])
                if len(citations[word]) < 3:
                    citations[word].append(chunk.chunk_id)

        preferred_tokens = [token.lower() for token in request.taxonomy_terms if token.lower() in token_counter]
        ranked_tokens = preferred_tokens + [
            token for token, _ in token_counter.most_common(request.top_n_topics * 2) if token not in preferred_tokens
        ]

        topics: list[Topic] = []
        for idx, token in enumerate(ranked_tokens[: request.top_n_topics], start=1):
            confidence = min(0.99, 0.4 + (token_counter[token] / max(1, len(ingestion.chunks) * 5)))
            topics.append(
                Topic(
                    topic_id=f"topic-{idx}",
                    title=token.replace("-", " ").title(),
                    key_concepts=[token, f"{token} fundamentals", f"{token} application"],
                    confidence=round(confidence, 2),
                    citations=citations.get(token, []),
                    lesson_order=idx,
                )
            )

        prerequisites = {
            topic.topic_id: [topics[idx - 2].topic_id] if idx > 1 else []
            for idx, topic in enumerate(topics, start=1)
        }

        response = TopicExtractionResponse(
            extraction_id=f"tex-{uuid4()}",
            ingestion_id=request.ingestion_id,
            topics=topics,
            prerequisites=prerequisites,
            created_at=self._now(),
        )
        self._topic_extractions[response.extraction_id] = response
        return response

    def generate_lessons(self, request: LessonGenerationRequest) -> LessonGenerationResponse:
        extraction = self._topic_extractions.get(request.extraction_id)
        if not extraction:
            raise HTTPException(status_code=404, detail="Topic extraction not found")

        # LLM path — falls through to template generation on failure or absent client
        if self._llm_client is not None:
            llm_result = self._generate_lessons_llm(request, extraction)
            if llm_result is not None:
                return llm_result

        lessons: list[Lesson] = []
        for topic in extraction.topics:
            lesson = Lesson(
                lesson_id=f"lesson-{topic.lesson_order}",
                topic_id=topic.topic_id,
                title=f"{topic.title}: Guided Lesson",
                objectives=[
                    f"Define {topic.title.lower()}",
                    f"Apply {topic.title.lower()} concepts to practical scenarios",
                ],
                explanation=f"This lesson introduces {topic.title.lower()} using structured examples and concise definitions.",
                worked_example=f"Walk through a realistic {topic.title.lower()} scenario from analysis to outcome.",
                practice_tasks=[
                    f"List 3 important ideas about {topic.title.lower()}",
                    f"Explain how {topic.title.lower()} impacts course outcomes",
                ],
                summary=f"You now understand the core principles of {topic.title.lower()}.",
                estimated_duration_minutes=15 if request.learner_level == DifficultyLevel.BEGINNER else 10,
            )
            lessons.append(lesson)

        response = LessonGenerationResponse(
            generation_id=f"lgen-{uuid4()}",
            extraction_id=request.extraction_id,
            lessons=lessons,
            created_at=self._now(),
        )
        self._lesson_generations[response.generation_id] = response
        return response

    def generate_quizzes(self, request: QuizGenerationRequest) -> QuizGenerationResponse:
        lesson_generation = self._lesson_generations.get(request.generation_id)
        if not lesson_generation:
            raise HTTPException(status_code=404, detail="Lesson generation not found")

        # LLM path — falls through to template generation on failure or absent client
        if self._llm_client is not None:
            llm_result = self._generate_quizzes_llm(request, lesson_generation)
            if llm_result is not None:
                return llm_result

        questions: list[QuizQuestion] = []
        difficulty_cycle = [DifficultyLevel.BEGINNER, DifficultyLevel.INTERMEDIATE, DifficultyLevel.ADVANCED]

        for lesson in lesson_generation.lessons:
            for index in range(request.questions_per_lesson):
                difficulty = difficulty_cycle[index % len(difficulty_cycle)]
                prompt = f"Which statement best describes {lesson.title.lower()}?"
                answer = f"{lesson.title} focuses on practical understanding and application."
                options = [
                    answer,
                    "It avoids examples and only defines terms.",
                    "It replaces assessment with unstructured discussion.",
                    "It excludes learner objectives and outcomes.",
                ]
                questions.append(
                    QuizQuestion(
                        question_id=f"{lesson.lesson_id}-q{index + 1}",
                        lesson_id=lesson.lesson_id,
                        prompt=prompt,
                        options=options,
                        answer=answer,
                        rationale=f"The lesson structure includes objectives, explanation, examples, and practice for {lesson.title.lower()}.",
                        difficulty=difficulty,
                    )
                )

        coverage_percent = round(100.0 if lesson_generation.lessons else 0.0, 2)
        response = QuizGenerationResponse(
            quiz_id=f"quiz-{uuid4()}",
            generation_id=request.generation_id,
            questions=questions,
            coverage_percent=coverage_percent,
            estimated_completion_minutes=max(1, len(questions) * 2),
            created_at=self._now(),
        )
        return response

    def run_pipeline(self, request: PipelineRequest) -> PipelineResponse:
        ingestion = self.ingest_documents(request.ingestion)
        topic_request = request.topic_extraction.model_copy(update={"ingestion_id": ingestion.ingestion_id})
        topic_response = self.extract_topics(topic_request)

        lesson_request = request.lesson_generation.model_copy(update={"extraction_id": topic_response.extraction_id})
        lesson_response = self.generate_lessons(lesson_request)

        quiz_request = request.quiz_generation.model_copy(update={"generation_id": lesson_response.generation_id})
        quiz_response = self.generate_quizzes(quiz_request)

        return PipelineResponse(
            ingestion=ingestion,
            topic_extraction=topic_response,
            lesson_generation=lesson_response,
            quiz_generation=quiz_response,
        )

    # ------------------------------------------------------------------
    # LLM-backed pipeline stages (all return None on failure → fallback)
    # ------------------------------------------------------------------

    def _extract_topics_llm(
        self,
        request: TopicExtractionRequest,
        ingestion: IngestionResponse,
    ) -> TopicExtractionResponse | None:
        assert self._llm_client is not None
        combined = "\n\n".join(c.text for c in ingestion.chunks)[:_LLM_CONTEXT_CHAR_LIMIT]
        taxonomy_hint = (
            f"Prefer topics from this taxonomy: {', '.join(request.taxonomy_terms)}.\n"
            if request.taxonomy_terms
            else ""
        )
        prompt = (
            f"Extract the top {request.top_n_topics} educational topics from the content below.\n"
            f"{taxonomy_hint}"
            f"Return a JSON array of objects with these exact keys:\n"
            f'  "title": string\n'
            f'  "key_concepts": array of 2–4 strings\n'
            f'  "confidence": float 0.0–1.0\n'
            f"No explanation. JSON only.\n\n"
            f"CONTENT:\n{combined}"
        )
        items = self._llm_client.complete_json(
            prompt=prompt,
            system_prompt="You are an expert educational content analyst. Output strict JSON only.",
        )
        if not isinstance(items, list) or not items:
            return None

        topics: list[Topic] = []
        for idx, item in enumerate(items[: request.top_n_topics], start=1):
            if not isinstance(item, dict):
                continue
            topics.append(
                Topic(
                    topic_id=f"topic-{idx}",
                    title=str(item.get("title", f"Topic {idx}")),
                    key_concepts=[str(c) for c in item.get("key_concepts", [])[:4]],
                    confidence=round(float(item.get("confidence", 0.8)), 2),
                    citations=[],
                    lesson_order=idx,
                )
            )
        if not topics:
            return None

        prerequisites = {
            t.topic_id: [topics[i - 2].topic_id] if i > 1 else []
            for i, t in enumerate(topics, start=1)
        }
        response = TopicExtractionResponse(
            extraction_id=f"tex-{uuid4()}",
            ingestion_id=request.ingestion_id,
            topics=topics,
            prerequisites=prerequisites,
            created_at=self._now(),
        )
        self._topic_extractions[response.extraction_id] = response
        return response

    def _generate_lessons_llm(
        self,
        request: LessonGenerationRequest,
        extraction: TopicExtractionResponse,
    ) -> LessonGenerationResponse | None:
        assert self._llm_client is not None
        topic_list = "\n".join(
            f"- {t.topic_id}: {t.title} (concepts: {', '.join(t.key_concepts)})"
            for t in extraction.topics
        )
        level = request.learner_level.value if hasattr(request.learner_level, "value") else str(request.learner_level)
        prompt = (
            f"Generate one lesson per topic for a {level}-level course.\n"
            f"Topics:\n{topic_list}\n\n"
            f"Return a JSON array, one object per topic, with these exact keys:\n"
            f'  "topic_id": string (match the topic_id above)\n'
            f'  "title": string\n'
            f'  "objectives": array of 2 strings\n'
            f'  "explanation": string (2–4 sentences)\n'
            f'  "worked_example": string (1–2 sentences)\n'
            f'  "practice_tasks": array of 2 strings\n'
            f'  "summary": string (1 sentence)\n'
            f'  "estimated_duration_minutes": integer\n'
            f"No explanation. JSON only."
        )
        items = self._llm_client.complete_json(
            prompt=prompt,
            system_prompt="You are a professional instructional designer. Output strict JSON only.",
        )
        if not isinstance(items, list) or not items:
            return None

        topic_map = {t.topic_id: t for t in extraction.topics}
        lessons: list[Lesson] = []
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            tid = str(item.get("topic_id", f"topic-{idx}"))
            topic = topic_map.get(tid)
            lessons.append(
                Lesson(
                    lesson_id=f"lesson-{idx}",
                    topic_id=tid,
                    title=str(item.get("title", topic.title if topic else f"Lesson {idx}")),
                    objectives=[str(o) for o in item.get("objectives", [])[:2]],
                    explanation=str(item.get("explanation", "")),
                    worked_example=str(item.get("worked_example", "")),
                    practice_tasks=[str(t) for t in item.get("practice_tasks", [])[:2]],
                    summary=str(item.get("summary", "")),
                    estimated_duration_minutes=int(item.get("estimated_duration_minutes", 15)),
                )
            )
        if not lessons:
            return None

        response = LessonGenerationResponse(
            generation_id=f"lgen-{uuid4()}",
            extraction_id=request.extraction_id,
            lessons=lessons,
            created_at=self._now(),
        )
        self._lesson_generations[response.generation_id] = response
        return response

    def _generate_quizzes_llm(
        self,
        request: QuizGenerationRequest,
        lesson_generation: LessonGenerationResponse,
    ) -> QuizGenerationResponse | None:
        assert self._llm_client is not None
        lesson_summaries = "\n".join(
            f"- {l.lesson_id}: {l.title} — {l.summary}"
            for l in lesson_generation.lessons
        )
        n = request.questions_per_lesson
        prompt = (
            f"Generate {n} multiple-choice quiz question(s) per lesson.\n"
            f"Lessons:\n{lesson_summaries}\n\n"
            f"Return a JSON array of question objects with these exact keys:\n"
            f'  "lesson_id": string (match above)\n'
            f'  "prompt": string (the question)\n'
            f'  "options": array of exactly 4 strings\n'
            f'  "answer": string (must match one of the options exactly)\n'
            f'  "rationale": string (1 sentence)\n'
            f'  "difficulty": "beginner" | "intermediate" | "advanced"\n'
            f"No explanation. JSON only."
        )
        items = self._llm_client.complete_json(
            prompt=prompt,
            system_prompt="You are a professional assessment writer. Output strict JSON only.",
        )
        if not isinstance(items, list) or not items:
            return None

        questions: list[QuizQuestion] = []
        for idx, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            raw_diff = str(item.get("difficulty", "beginner")).lower()
            difficulty = (
                DifficultyLevel(raw_diff)
                if raw_diff in DifficultyLevel._value2member_map_
                else DifficultyLevel.BEGINNER
            )
            questions.append(
                QuizQuestion(
                    question_id=f"{item.get('lesson_id', 'lesson-1')}-q{idx}",
                    lesson_id=str(item.get("lesson_id", "")),
                    prompt=str(item.get("prompt", "")),
                    options=[str(o) for o in item.get("options", [])[:4]],
                    answer=str(item.get("answer", "")),
                    rationale=str(item.get("rationale", "")),
                    difficulty=difficulty,
                )
            )
        if not questions:
            return None

        coverage_percent = round(100.0, 2)
        return QuizGenerationResponse(
            quiz_id=f"quiz-{uuid4()}",
            generation_id=request.generation_id,
            questions=questions,
            coverage_percent=coverage_percent,
            estimated_completion_minutes=max(1, len(questions) * 2),
            created_at=self._now(),
        )

    @staticmethod
    def _chunk_content(content: str, max_chunk_size: int) -> list[str]:
        paragraphs = [segment.strip() for segment in re.split(r"\n{2,}", content) if segment.strip()]
        if not paragraphs:
            return [content.strip()] if content.strip() else []

        chunks: list[str] = []
        for paragraph in paragraphs:
            if len(paragraph) <= max_chunk_size:
                chunks.append(paragraph)
                continue
            words = paragraph.split()
            current: list[str] = []
            for word in words:
                current.append(word)
                if len(" ".join(current)) >= max_chunk_size:
                    chunks.append(" ".join(current))
                    current = []
            if current:
                chunks.append(" ".join(current))
        return chunks
