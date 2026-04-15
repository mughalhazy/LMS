from datetime import datetime, timedelta, timezone

import pytest

from src.models import QuestionType, QuizDefinition, QuizOption, QuizQuestion
from src.quiz_engine import QuizEngine, SessionExpiredError


def build_quiz(randomize: bool = True) -> QuizDefinition:
    return QuizDefinition(
        quiz_id="quiz-1",
        tenant_id="tenant-1",
        title="Python Basics",
        duration_seconds=300,
        randomize_questions=randomize,
        questions=[
            QuizQuestion(
                question_id="q1",
                prompt="2 + 2 = ?",
                question_type=QuestionType.SINGLE_CHOICE,
                points=2,
                options=[
                    QuizOption("o1", "3"),
                    QuizOption("o2", "4", is_correct=True),
                ],
            ),
            QuizQuestion(
                question_id="q2",
                prompt="Select valid Python data types",
                question_type=QuestionType.MULTIPLE_CHOICE,
                points=3,
                options=[
                    QuizOption("o3", "list", is_correct=True),
                    QuizOption("o4", "dictionary", is_correct=True),
                    QuizOption("o5", "spreadsheet"),
                ],
            ),
        ],
    )


def test_rendering_hides_correctness_flags() -> None:
    engine = QuizEngine()
    engine.register_quiz(build_quiz(randomize=False))

    session = engine.start_session("tenant-1", "quiz-1", "user-1")
    rendered = engine.render_quiz(session.session_id)

    assert rendered["questions"][0]["question_id"] == "q1"
    assert rendered["questions"][1]["question_id"] == "q2"
    assert "is_correct" not in rendered["questions"][0]["options"][0]


def test_question_randomization_is_seeded() -> None:
    engine = QuizEngine()
    engine.register_quiz(build_quiz(randomize=True))

    first = engine.start_session("tenant-1", "quiz-1", "user-1", seed=2)
    second = engine.start_session("tenant-1", "quiz-1", "user-2", seed=2)
    third = engine.start_session("tenant-1", "quiz-1", "user-3", seed=7)

    assert first.ordered_question_ids == second.ordered_question_ids
    assert first.ordered_question_ids != third.ordered_question_ids


def test_timer_logic_blocks_expired_submissions() -> None:
    engine = QuizEngine()
    engine.register_quiz(build_quiz(randomize=False))

    started_at = datetime.now(tz=timezone.utc) - timedelta(minutes=10)
    session = engine.start_session("tenant-1", "quiz-1", "user-1", started_at=started_at)

    assert engine.render_quiz(session.session_id)["time_remaining_seconds"] == 0
    with pytest.raises(SessionExpiredError):
        engine.submit_answer(session.session_id, "q1", ["o2"])


def test_scoring_engine_calculates_totals_and_pass_fail() -> None:
    engine = QuizEngine(pass_threshold_percent=60)
    engine.register_quiz(build_quiz(randomize=False))

    session = engine.start_session("tenant-1", "quiz-1", "user-1")
    engine.submit_answer(session.session_id, "q1", ["o2"])
    engine.submit_answer(session.session_id, "q2", ["o3", "o4"])

    score = engine.submit_quiz(session.session_id)
    assert score.score == 5
    assert score.max_score == 5
    assert score.percentage == 100
    assert score.passed is True


def test_scoring_engine_requires_exact_multi_select() -> None:
    engine = QuizEngine(pass_threshold_percent=80)
    engine.register_quiz(build_quiz(randomize=False))

    session = engine.start_session("tenant-1", "quiz-1", "user-1")
    engine.submit_answer(session.session_id, "q1", ["o2"])
    engine.submit_answer(session.session_id, "q2", ["o3", "o4", "o5"])

    score = engine.submit_quiz(session.session_id)
    assert score.score == 2
    assert score.max_score == 5
    assert score.percentage == 40
    assert score.passed is False
