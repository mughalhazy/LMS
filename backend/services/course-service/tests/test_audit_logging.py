from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

_APP_ROOT = Path(__file__).resolve().parents[1] / "app"


def _load_module(module_name: str, path: Path):
    spec = spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {module_name} from {path}")
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_SCHEMAS = _load_module("course_service_schemas", _APP_ROOT / "schemas.py")
_SERVICE = _load_module("course_service_service", _APP_ROOT / "service.py")
CreateCourseRequest = _SCHEMAS.CreateCourseRequest
CourseService = _SERVICE.CourseService


def test_course_creation_is_audited_with_required_fields() -> None:
    service = CourseService()
    service.create_course(CreateCourseRequest(tenant_id="tenant-a", created_by="creator-1", title="Course"))

    event = service.audit_logger.list_events()[-1]
    assert event.event_type == "course.created"
    assert event.tenant_id == "tenant-a"
    assert event.actor_id == "creator-1"
    assert event.timestamp is not None
    assert event.destination == "loki"
