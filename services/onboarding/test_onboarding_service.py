from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

MODULE_PATH = ROOT / "services/onboarding/service.py"

spec = importlib.util.spec_from_file_location("onboarding_test_module", MODULE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError("Unable to load onboarding module")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

OnboardingRequest = module.OnboardingRequest
OnboardingService = module.OnboardingService
ConfigService = module.ConfigService

from shared.models.config import ConfigLevel, ConfigOverride, ConfigScope


def _request() -> OnboardingRequest:
    return OnboardingRequest(
        tenant_id="tenant-1",
        learner_id="learner-1",
        country_code="PK",
        segment_id="academy",
        whatsapp_number="+923001112233",
        teacher_id="teacher-22",
    )


def test_start_defaults_to_instant_setup_and_whatsapp() -> None:
    service = OnboardingService()

    session = service.start(_request())

    assert session.onboarding_mode == "whatsapp_first"
    assert session.status == "completed"
    assert session.metadata["manual_setup_required"] is False
    assert session.metadata["dashboard_required"] is False


def test_start_honors_dashboard_override_policy() -> None:
    config = ConfigService()
    config.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.TENANT, scope_id="tenant-1"),
            behavior_tuning={
                "onboarding": {
                    "instant_setup": False,
                    "preferred_channel": "dashboard",
                    "dashboard_required": True,
                }
            },
        )
    )

    service = OnboardingService(config_service=config)
    session = service.start(_request())

    assert session.onboarding_mode == "dashboard"
    assert session.metadata["dashboard_required"] is True


def test_create_instant_academy_bootstraps_defaults() -> None:
    service = OnboardingService()

    session = service.create_instant_academy(_request())

    assert session.metadata["default_branch"]["branch_id"].startswith("br_tenant-1")
    assert session.metadata["default_batch"]["batch_id"].startswith("batch_tenant-1")
    assert session.metadata["initial_teacher"]["teacher_id"] == "teacher-22"
    assert session.metadata["capabilities"]["attendance_tracking"] is True
