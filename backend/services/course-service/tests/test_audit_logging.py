import sys
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType

_APP_ROOT = Path(__file__).resolve().parents[1] / "app"
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


def _load_module(module_name: str, path: Path, package_name: str):
    if package_name not in sys.modules:
        package = ModuleType(package_name)
        package.__path__ = [str(path.parent)]  # type: ignore[attr-defined]
        sys.modules[package_name] = package
    spec = spec_from_file_location(
        f"{package_name}.{module_name}",
        path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module {module_name} from {path}")
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_SCHEMAS = _load_module("schemas", _APP_ROOT / "schemas.py", "course_service_app")
_SERVICE = _load_module("service", _APP_ROOT / "service.py", "course_service_app")
CreateCourseRequest = _SCHEMAS.CreateCourseRequest
CourseService = _SERVICE.CourseService


def test_course_creation_is_audited_with_required_fields() -> None:
    service = CourseService()
    service.create_course(CreateCourseRequest(tenant_id="tenant-a", created_by="creator-1", title="Course", plan_type="pro"))

    event = service.audit_logger.list_events()[-1]
    assert event.event_type == "course.created"
    assert event.tenant_id == "tenant-a"
    assert event.actor_id == "creator-1"
    assert event.timestamp is not None
    assert event.destination == "loki"
