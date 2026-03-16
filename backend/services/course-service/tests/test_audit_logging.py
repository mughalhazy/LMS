from app.schemas import CreateCourseRequest
from app.service import CourseService


def test_course_creation_is_audited_with_required_fields() -> None:
    service = CourseService()
    service.create_course(CreateCourseRequest(tenant_id="tenant-a", created_by="creator-1", title="Course"))

    event = service.audit_logger.list_events()[-1]
    assert event.event_type == "course.creation"
    assert event.tenant_id == "tenant-a"
    assert event.actor_id == "creator-1"
    assert event.timestamp is not None
    assert event.destination == "loki"
