from app.schemas import AnswerSubmission, RecordAnswersRequest, StartAttemptRequest
from app.service import AttemptService


def test_assessment_submission_is_audited_with_required_fields() -> None:
    service = AttemptService()
    attempt = service.start_attempt(
        StartAttemptRequest(
            tenant_id="tenant-a",
            learner_id="learner-1",
            assessment_id="asm-1",
            started_by="learner-1",
        )
    )

    service.record_answers(
        attempt.attempt_id,
        RecordAnswersRequest(tenant_id="tenant-a", answers=[AnswerSubmission(question_id="q1", response="a")]),
    )

    event = service.audit_logger.list_events()[-1]
    assert event.event_type == "assessment.submission"
    assert event.tenant_id == "tenant-a"
    assert event.actor_id == "learner-1"
    assert event.timestamp is not None
    assert event.destination == "loki"
