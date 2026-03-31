from src.repository import InMemoryAssessmentRepository
from src.service import AssessmentPublishValidationError, AssessmentService, TenantScopeError


def _service() -> AssessmentService:
    return AssessmentService(InMemoryAssessmentRepository())


def test_assessment_creation_with_dependencies() -> None:
    service = _service()

    bank = service.create_question_bank(
        tenant_id="tenant-a",
        name="Python Basics",
        description="Core Python questions",
        course_id="course-1",
        created_by="author-1",
    )
    rule = service.create_grading_rule(
        tenant_id="tenant-a",
        name="Default grading",
        pass_threshold=70,
        negative_marking_ratio=0.25,
        max_attempts=3,
        allow_partial_credit=True,
        late_penalty_percent=10,
        created_by="author-1",
    )

    created = service.create_assessment(
        tenant_id="tenant-a",
        course_id="course-1",
        title="Week 1 Quiz",
        description="Intro assessment",
        assessment_type="quiz",
        time_limit_minutes=30,
        question_bank_id=bank["question_bank_id"],
        grading_rule_id=rule["grading_rule_id"],
        created_by="author-1",
    )

    assert created["status"] == "draft"
    assert created["question_bank_id"] == bank["question_bank_id"]
    assert created["grading_rule_id"] == rule["grading_rule_id"]


def test_publish_assessment_success() -> None:
    service = _service()

    bank = service.create_question_bank(
        tenant_id="tenant-a",
        name="Networking",
        description="Networking bank",
        created_by="author-1",
    )
    service.add_question_bank_item(
        tenant_id="tenant-a",
        question_bank_id=bank["question_bank_id"],
        prompt="What is TCP?",
        question_type="single_choice",
        options=["A protocol", "A server", "A browser"],
        correct_answer="A protocol",
        objective_tag="networking.fundamentals",
        difficulty="easy",
        points=2,
    )
    rule = service.create_grading_rule(
        tenant_id="tenant-a",
        name="Strict grading",
        pass_threshold=80,
        negative_marking_ratio=0,
        max_attempts=1,
        allow_partial_credit=False,
        late_penalty_percent=0,
        created_by="author-1",
    )
    created = service.create_assessment(
        tenant_id="tenant-a",
        course_id="course-2",
        title="Network Quiz",
        description="Quiz",
        assessment_type="quiz",
        time_limit_minutes=20,
        question_bank_id=bank["question_bank_id"],
        grading_rule_id=rule["grading_rule_id"],
        created_by="author-1",
    )

    published = service.publish_assessment(
        tenant_id="tenant-a",
        assessment_id=created["assessment_id"],
        published_by="instructor-1",
    )

    assert published["status"] == "published"
    assert published["published_by"] == "instructor-1"


def test_publish_requires_question_and_grading() -> None:
    service = _service()
    created = service.create_assessment(
        tenant_id="tenant-a",
        course_id="course-9",
        title="Broken quiz",
        description="missing dependencies",
        assessment_type="quiz",
        time_limit_minutes=15,
        created_by="author-1",
    )

    try:
        service.publish_assessment(
            tenant_id="tenant-a",
            assessment_id=created["assessment_id"],
            published_by="instructor-1",
        )
    except AssessmentPublishValidationError as exc:
        assert "question bank" in str(exc)
    else:
        raise AssertionError("publish_assessment should require question bank")


def test_tenant_isolation_on_question_bank_mutation() -> None:
    service = _service()
    bank = service.create_question_bank(
        tenant_id="tenant-a",
        name="Shared",
        description="Do not cross mutate",
        created_by="author-1",
    )

    try:
        service.add_question_bank_item(
            tenant_id="tenant-b",
            question_bank_id=bank["question_bank_id"],
            prompt="Attempt cross-tenant write",
            question_type="free_text",
            options=[],
            correct_answer="No",
            objective_tag="security",
            difficulty="medium",
            points=1,
        )
    except TenantScopeError:
        return
    else:
        raise AssertionError("cross-tenant write should fail")
