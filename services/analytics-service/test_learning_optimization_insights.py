import importlib.util
import sys
from pathlib import Path
from types import ModuleType

_SERVICE_PATH = Path(__file__).with_name("service.py")
_MODELS_PATH = Path(__file__).with_name("models.py")
_PACKAGE_NAME = "analytics_service_pkg"

package = ModuleType(_PACKAGE_NAME)
package.__path__ = [str(Path(__file__).parent)]  # type: ignore[attr-defined]
sys.modules[_PACKAGE_NAME] = package

service_spec = importlib.util.spec_from_file_location(f"{_PACKAGE_NAME}.service", _SERVICE_PATH)
models_spec = importlib.util.spec_from_file_location(f"{_PACKAGE_NAME}.models", _MODELS_PATH)
if service_spec is None or service_spec.loader is None or models_spec is None or models_spec.loader is None:
    raise RuntimeError("Unable to load analytics-service modules")

service_module = importlib.util.module_from_spec(service_spec)
models_module = importlib.util.module_from_spec(models_spec)
sys.modules[service_spec.name] = service_module
sys.modules[models_spec.name] = models_module
models_spec.loader.exec_module(models_module)
service_spec.loader.exec_module(service_module)

AnalyticsService = service_module.AnalyticsService
ExamEngineSnapshot = models_module.ExamEngineSnapshot
LearningOptimizationInsightRequest = models_module.LearningOptimizationInsightRequest
ProgressSnapshot = models_module.ProgressSnapshot
SystemOfRecordSnapshot = models_module.SystemOfRecordSnapshot


def test_generate_learning_optimization_insight_with_integrated_sources() -> None:
    service = AnalyticsService()
    req = LearningOptimizationInsightRequest(
        system_of_record=SystemOfRecordSnapshot(
            learner_id="learner-1",
            tenant_id="tenant-1",
            lifecycle_state="active",
            attendance_rate=62,
            overdue_balance=1200,
        ),
        progress=ProgressSnapshot(
            completion_rate=38,
            weekly_active_minutes=55,
            missed_deadlines=3,
            activity_streak_days=1,
        ),
        exam_engine=ExamEngineSnapshot(
            average_score=49,
            failed_attempts=2,
            no_show_count=1,
            trend_delta=-6,
        ),
        metadata={"cohort_id": "cohort-risk-a"},
    )

    insight = service.generate_learning_optimization_insight(req)
    assert insight.risk_band in {"medium", "high"}
    assert insight.dropout_risk_score > 0
    assert insight.engagement_risk_score > 0
    assert insight.recommendation_hooks.recommendation_service_input["tenant_id"] == "tenant-1"
    assert len(insight.teacher_actions) >= 2
    assert len(insight.operations_actions) >= 2
    assert len(insight.owner_actions) >= 2
