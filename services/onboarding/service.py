from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.config import ConfigResolutionContext

_ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, relative_path: str):
    module_path = _ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_ConfigModule = _load_module("config_service_module_for_onboarding", "services/config-service/service.py")
ConfigService = _ConfigModule.ConfigService


@dataclass(frozen=True)
class OnboardingRequest:
    tenant_id: str
    learner_id: str
    country_code: str
    segment_id: str
    whatsapp_number: str


@dataclass(frozen=True)
class OnboardingSession:
    tenant_id: str
    learner_id: str
    channel: str
    instant_setup: bool
    steps: tuple[str, ...]
    metadata: dict[str, str] = field(default_factory=dict)


class OnboardingService:
    """Simple onboarding flow with instant setup and WhatsApp-first defaults."""

    def __init__(self, *, config_service: ConfigService | None = None) -> None:
        self._config_service = config_service or ConfigService()

    def _resolve_policy(self, request: OnboardingRequest) -> dict[str, object]:
        effective = self._config_service.resolve(
            ConfigResolutionContext(
                tenant_id=request.tenant_id,
                country_code=request.country_code,
                segment_id=request.segment_id,
            )
        )
        return effective.behavior_tuning.get("onboarding", {})

    def start(self, request: OnboardingRequest) -> OnboardingSession:
        policy = self._resolve_policy(request)

        instant_setup = bool(policy.get("instant_setup", True))
        preferred_channel = str(policy.get("preferred_channel", "whatsapp")).lower()
        channel = "whatsapp" if preferred_channel == "whatsapp" else "whatsapp"

        steps = ("collect_profile", "verify_whatsapp", "complete") if instant_setup else (
            "collect_profile",
            "verify_whatsapp",
            "manual_review",
            "complete",
        )

        return OnboardingSession(
            tenant_id=request.tenant_id,
            learner_id=request.learner_id,
            channel=channel,
            instant_setup=instant_setup,
            steps=steps,
            metadata={"whatsapp_number": request.whatsapp_number},
        )
