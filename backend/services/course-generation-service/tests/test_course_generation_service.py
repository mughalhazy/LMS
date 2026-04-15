from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def _sample_ingestion_payload() -> dict:
    return {
        "tenant_id": "tenant-1",
        "course_id": "course-101",
        "course_level": "beginner",
        "audience": "new hires",
        "language": "en",
        "documents": [
            {
                "document_id": "doc-1",
                "source_type": "pdf",
                "title": "Safety Basics",
                "content": "Safety protocols define baseline procedures for teams.\n\nRisk assessment helps identify hazards before incidents.",
            },
            {
                "document_id": "doc-2",
                "source_type": "docx",
                "title": "Incident Response",
                "content": "Incident response aligns communication, triage, and escalation.\n\nPost-incident review improves prevention plans.",
            },
        ],
    }


def test_full_pipeline_endpoint() -> None:
    pipeline_payload = {
        "ingestion": _sample_ingestion_payload(),
        "topic_extraction": {
            "ingestion_id": "placeholder",
            "course_goals": ["Understand safety", "Handle incidents"],
            "taxonomy_terms": ["safety", "incident", "risk"],
            "top_n_topics": 5,
        },
        "lesson_generation": {
            "extraction_id": "placeholder",
            "learner_level": "beginner",
            "pacing": "standard",
            "locale": "en-US",
        },
        "quiz_generation": {
            "generation_id": "placeholder",
            "questions_per_lesson": 2,
        },
    }

    response = client.post("/course-generation/pipeline:run", json=pipeline_payload)
    assert response.status_code == 200

    body = response.json()
    assert body["ingestion"]["metadata_index"]["document_count"] == "2"
    assert len(body["ingestion"]["chunks"]) >= 2
    assert len(body["topic_extraction"]["topics"]) >= 1
    assert len(body["lesson_generation"]["lessons"]) == len(body["topic_extraction"]["topics"])
    assert len(body["quiz_generation"]["questions"]) == len(body["lesson_generation"]["lessons"]) * 2


def test_stage_endpoints_with_missing_dependencies() -> None:
    missing_topic = client.post(
        "/course-generation/topics:extract",
        json={"ingestion_id": "missing", "top_n_topics": 3},
    )
    assert missing_topic.status_code == 404

    missing_lesson = client.post(
        "/course-generation/lessons:generate",
        json={"extraction_id": "missing", "learner_level": "advanced"},
    )
    assert missing_lesson.status_code == 404

    missing_quiz = client.post(
        "/course-generation/quizzes:generate",
        json={"generation_id": "missing", "questions_per_lesson": 1},
    )
    assert missing_quiz.status_code == 404
