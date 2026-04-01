import importlib.util
from pathlib import Path

_SERVICE_PATH = Path(__file__).with_name("service.py")
_spec = importlib.util.spec_from_file_location("analytics_service_module", _SERVICE_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError("Unable to load analytics service module")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
AnalyticsService = _module.AnalyticsService

__all__ = ["AnalyticsService"]
