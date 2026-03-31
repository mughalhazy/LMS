from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from shared.models.config import ConfigLevel, ConfigOverride, ConfigScope

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


def _request() -> OnboardingRequest:
    return OnboardingRequest(
        tenant_id="tenant-1",
        learner_id="learner-1",
        country_code="IN",
        segment_id="k12",
        whatsapp_number="+919999999999",
    )


def test_start_defaults_to_instant_setup_and_whatsapp() -> None:
    service = OnboardingService()

    session = service.start(_request())

    assert session.instant_setup is True
    assert session.channel == "whatsapp"
    assert session.steps == ("collect_profile", "verify_whatsapp", "complete")


def test_start_honors_config_service_policy_override() -> None:
    config = ConfigService()
    config.upsert_override(
        ConfigOverride(
            scope=ConfigScope(level=ConfigLevel.TENANT, scope_id="tenant-1"),
            behavior_tuning={
                "onboarding": {
                    "instant_setup": False,
                    "preferred_channel": "whatsapp",
                }
            },
        )
    )

    service = OnboardingService(config_service=config)
    session = service.start(_request())

    assert session.instant_setup is False
    assert session.channel == "whatsapp"
    assert session.steps == ("collect_profile", "verify_whatsapp", "manual_review", "complete")
