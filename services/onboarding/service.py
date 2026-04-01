from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.config import ConfigLevel, ConfigOverride, ConfigResolutionContext, ConfigScope
from shared.models.onboarding import OnboardingSession

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
_WorkflowModule = _load_module("workflow_engine_module_for_onboarding", "services/workflow-engine/service.py")
ConfigService = _ConfigModule.ConfigService
WorkflowEngine = _WorkflowModule.WorkflowEngine


@dataclass(frozen=True)
class OnboardingRequest:
    tenant_id: str
    learner_id: str
    country_code: str
    segment_id: str
    whatsapp_number: str
    teacher_id: str = "teacher-default"


class OnboardingService:
    """Instant academy onboarding with WhatsApp-first defaults."""

    def __init__(
        self,
        *,
        config_service: ConfigService | None = None,
        workflow_engine: WorkflowEngine | None = None,
    ) -> None:
        self._config_service = config_service or ConfigService()
        self._workflow_engine = workflow_engine or WorkflowEngine(config_service=self._config_service)

    def _resolve_policy(self, request: OnboardingRequest) -> dict[str, object]:
        effective = self._config_service.resolve(
            ConfigResolutionContext(
                tenant_id=request.tenant_id,
                country_code=request.country_code,
                segment_id=request.segment_id,
            )
        )
        return effective.behavior_tuning.get("onboarding", {})

    def create_instant_academy(self, request: OnboardingRequest) -> OnboardingSession:
        onboarding_id = f"onb_{uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        mode = "whatsapp_first"

        initial_config = self.apply_pakistan_default_config(request=request)
        capabilities = self.bootstrap_default_capabilities(request=request)
        branch = self.create_default_branch(request=request)
        batch = self.create_default_batch(request=request, branch_id=branch["branch_id"])
        teacher_assignment = self.assign_initial_teacher(request=request, batch_id=batch["batch_id"])

        session = OnboardingSession(
            onboarding_id=onboarding_id,
            tenant_id=request.tenant_id,
            onboarding_mode=mode,
            status="completed",
            created_at=now,
            completed_at=now,
            initial_config=initial_config,
            metadata={
                "learner_id": request.learner_id,
                "whatsapp_number": request.whatsapp_number,
                "dashboard_required": False,
                "manual_setup_required": False,
                "capabilities": capabilities,
                "default_branch": branch,
                "default_batch": batch,
                "initial_teacher": teacher_assignment,
            },
        )
        return session

    def bootstrap_default_capabilities(self, *, request: OnboardingRequest) -> dict[str, bool]:
        capabilities = {
            "attendance_tracking": True,
            "fees_management": True,
            "notifications": True,
            "whatsapp_primary_interface": True,
        }
        self._config_service.upsert_override(
            ConfigOverride(
                scope=ConfigScope(level=ConfigLevel.TENANT, scope_id=request.tenant_id),
                capability_enabled=capabilities,
            )
        )
        self._workflow_engine.bootstrap_default_workflows()
        return capabilities

    def apply_pakistan_default_config(self, *, request: OnboardingRequest) -> dict[str, object]:
        behavior_tuning = {
            "onboarding": {
                "instant_setup": True,
                "preferred_channel": "whatsapp",
                "dashboard_required": False,
            },
            "communication": {"routing_priority": ["whatsapp", "sms", "email"]},
            "fees": {"currency": "PKR", "grace_period_days": 7},
            "attendance": {"mode": "daily"},
        }
        self._config_service.upsert_override(
            ConfigOverride(
                scope=ConfigScope(level=ConfigLevel.TENANT, scope_id=request.tenant_id),
                behavior_tuning=behavior_tuning,
            )
        )
        return behavior_tuning

    def create_default_branch(self, *, request: OnboardingRequest) -> dict[str, str]:
        return {
            "branch_id": f"br_{request.tenant_id}_main",
            "name": "Main Campus",
            "location": "Pakistan",
        }

    def create_default_batch(self, *, request: OnboardingRequest, branch_id: str) -> dict[str, str]:
        return {
            "batch_id": f"batch_{request.tenant_id}_001",
            "branch_id": branch_id,
            "name": "Foundation Batch",
        }

    def assign_initial_teacher(self, *, request: OnboardingRequest, batch_id: str) -> dict[str, str]:
        return {
            "teacher_id": request.teacher_id,
            "batch_id": batch_id,
            "assignment_role": "primary_teacher",
        }

    def start(self, request: OnboardingRequest) -> OnboardingSession:
        policy = self._resolve_policy(request)
        instant_setup = bool(policy.get("instant_setup", True))
        preferred_channel = str(policy.get("preferred_channel", "whatsapp")).lower()

        if instant_setup and preferred_channel == "whatsapp":
            return self.create_instant_academy(request)

        fallback = self.create_instant_academy(request)
        return OnboardingSession(
            onboarding_id=fallback.onboarding_id,
            tenant_id=fallback.tenant_id,
            onboarding_mode="dashboard",
            status=fallback.status,
            created_at=fallback.created_at,
            completed_at=fallback.completed_at,
            initial_config=fallback.initial_config,
            metadata={**fallback.metadata, "dashboard_required": True},
        )
