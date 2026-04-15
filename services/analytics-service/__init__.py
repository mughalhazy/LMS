import importlib.util
import sys
from pathlib import Path

_SERVICE_PATH = Path(__file__).with_name("service.py")
_MODELS_PATH = Path(__file__).with_name("models.py")
_spec = importlib.util.spec_from_file_location("analytics_service_module", _SERVICE_PATH)
_models_spec = importlib.util.spec_from_file_location("analytics_service_models_module", _MODELS_PATH)
if _spec is None or _spec.loader is None or _models_spec is None or _models_spec.loader is None:
    raise RuntimeError("Unable to load analytics service module")
_module = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _module
_spec.loader.exec_module(_module)
_models_module = importlib.util.module_from_spec(_models_spec)
sys.modules[_models_spec.name] = _models_module
_models_spec.loader.exec_module(_models_module)
AnalyticsService = _module.AnalyticsService
ExamEngineSnapshot = _models_module.ExamEngineSnapshot
LearningOptimizationInsight = _models_module.LearningOptimizationInsight
LearningOptimizationInsightRequest = _models_module.LearningOptimizationInsightRequest
ProgressSnapshot = _models_module.ProgressSnapshot
RecommendationHooks = _models_module.RecommendationHooks
SystemOfRecordSnapshot = _models_module.SystemOfRecordSnapshot
InstitutionBenchmark = _models_module.InstitutionBenchmark
StudentBenchmark = _models_module.StudentBenchmark
TeacherBenchmark = _models_module.TeacherBenchmark
TeacherPerformanceSnapshot = _models_module.TeacherPerformanceSnapshot

__all__ = [
    "AnalyticsService",
    "ExamEngineSnapshot",
    "InstitutionBenchmark",
    "LearningOptimizationInsight",
    "LearningOptimizationInsightRequest",
    "ProgressSnapshot",
    "RecommendationHooks",
    "StudentBenchmark",
    "SystemOfRecordSnapshot",
    "TeacherBenchmark",
    "TeacherPerformanceSnapshot",
]
