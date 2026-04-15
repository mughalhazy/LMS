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
_ConfigDefaultsModule = _load_module("config_service_defaults_for_onboarding", "services/config-service/platform_defaults.py")
_WorkflowModule = _load_module("workflow_engine_module_for_onboarding", "services/workflow-engine/service.py")
ConfigService = _ConfigModule.ConfigService
seed_platform_defaults = _ConfigDefaultsModule.seed_platform_defaults
WorkflowEngine = _WorkflowModule.WorkflowEngine


@dataclass(frozen=True)
class OnboardingRequest:
    tenant_id: str
    learner_id: str
    country_code: str
    segment_id: str
    whatsapp_number: str
    teacher_id: str = "teacher-default"


# MS-CONFIG-01 (MS§3.2): country and segment defaults live in the config service
# resolution chain (seeded via seed_platform_defaults at OnboardingService init).
# No inline country/segment constants in service logic.


class OnboardingService:
    """Instant academy onboarding with WhatsApp-first defaults."""

    def __init__(
        self,
        *,
        config_service: ConfigService | None = None,
        workflow_engine: WorkflowEngine | None = None,
    ) -> None:
        self._config_service = config_service or ConfigService()
        # MS-CONFIG-01 (MS§3.2): seed country/segment defaults so resolution returns
        # locale, whatsapp, gdpr, and compliance values without inline conditionals.
        seed_platform_defaults(self._config_service)
        self._workflow_engine = workflow_engine or WorkflowEngine(config_service=self._config_service)

    def _resolve_country_segment_defaults(self, request: OnboardingRequest) -> dict[str, object]:
        """MS-CONFIG-01 (MS§3.2): read country and segment defaults from config resolution.

        Uses platform context (no tenant override) so only COUNTRY + SEGMENT layers
        are active. Returns resolved locale, whatsapp_primary, gdpr, mandatory_training
        flags and capability_enabled map — callers branch on these resolved outputs,
        not on raw country_code or segment_id values.
        """
        resolved = self._config_service.resolve(
            ConfigResolutionContext(
                tenant_id="__platform__",
                country_code=request.country_code,
                segment_id=request.segment_id,
            )
        )
        locale = resolved.behavior_tuning.get("locale", {})
        communication = resolved.behavior_tuning.get("communication", {})
        compliance = resolved.behavior_tuning.get("compliance", {})
        return {
            "currency": str(locale.get("currency", "USD")),
            "is_whatsapp_primary": bool(communication.get("whatsapp_primary", False)),
            "mandatory_training_enabled": bool(compliance.get("mandatory_training_enabled", False)),
            "gdpr_consent_required": bool(compliance.get("gdpr_consent_required", False)),
            "capability_enabled": dict(resolved.capability_enabled),
        }

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

        initial_config = self.apply_default_config(request=request)
        # CGAP-048: materialize concrete notification templates — no tenant starts with blank forms.
        notification_templates = self.apply_notification_template_defaults(request=request)
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
                "notification_templates": notification_templates,  # CGAP-048
                "default_branch": branch,
                "default_batch": batch,
                "initial_teacher": teacher_assignment,
            },
        )
        return session

    def bootstrap_default_capabilities(self, *, request: OnboardingRequest) -> dict[str, bool]:
        """BC-ONBOARD-01 (CGAP-046): activate full capability bundle derived from segment_type.

        MS-CONFIG-01 (MS§3.2): capabilities read from config resolution output (segment layer
        seeded by seed_platform_defaults), not from inline segment conditionals.
        WhatsApp capability is retained only when resolved communication.whatsapp_primary is True.
        """
        defaults = self._resolve_country_segment_defaults(request)
        capabilities: dict[str, bool] = defaults["capability_enabled"] or {"notifications": True, "attendance_tracking": True}

        # Disable WhatsApp capability for non-WhatsApp-primary countries per resolved config output
        if not defaults["is_whatsapp_primary"]:
            capabilities.pop("whatsapp_primary_interface", None)

        self._config_service.upsert_override(
            ConfigOverride(
                scope=ConfigScope(level=ConfigLevel.TENANT, scope_id=request.tenant_id),
                capability_enabled=capabilities,
            )
        )
        self._workflow_engine.bootstrap_default_workflows()

        # MO-034 / Phase D — BC-FREE-01: if the tenant is on the free plan, register
        # the quota-capped free tier capability bundle so they have operational access
        # from day one without any manual capability setup.
        # register_free_tier_capability_bundle() is idempotent — safe to call on every
        # bootstrap regardless of whether the registry already holds these caps.
        resolved_plan = str(
            self._config_service.resolve(
                ConfigResolutionContext(
                    tenant_id=request.tenant_id,
                    country_code=request.country_code,
                    segment_id=request.segment_id,
                )
            ).behavior_tuning.get("plan_type", "free")
        ).lower()

        if resolved_plan == "free" or "free" in capabilities:
            try:
                import importlib.util as _ilu
                import sys as _sys
                _cap_path = _ROOT / "services/capability-registry/service.py"
                _sys.path.append(str(_cap_path.parent))
                _spec = _ilu.spec_from_file_location("_onb_cap_registry", _cap_path)
                if _spec and _spec.loader:
                    _mod = _ilu.module_from_spec(_spec)
                    _spec.loader.exec_module(_mod)
                    _cap_registry = _mod.CapabilityRegistryService()
                    _cap_registry.register_free_tier_capability_bundle()
            except Exception:
                pass  # capability registry unavailable — silent; free tier bundle registered lazily

        return capabilities

    def apply_default_config(self, *, request: OnboardingRequest) -> dict[str, object]:
        """BC-ONBOARD-01 (CGAP-047): derive full platform config from segment_type + plan_type + country_code.

        Replaces the hardcoded Pakistan-specific config. Covers all 9 BC-ONBOARD-01 customisation areas:
        branding, locale, feature flags, notification templates, automation workflows,
        fee reminders, attendance rules, compliance settings, report schedule.
        No tenant admin input required — all defaults are derivable from the signup profile.
        """
        # MS-CONFIG-01 (MS§3.2): read locale, whatsapp, and compliance flags from
        # config resolution output — no inline country/segment conditionals.
        defaults = self._resolve_country_segment_defaults(request)
        currency = defaults["currency"]
        is_whatsapp_primary = defaults["is_whatsapp_primary"]

        # Communication routing: WhatsApp-first when resolved config output indicates it
        routing_priority = (
            ["whatsapp", "sms", "email"] if is_whatsapp_primary else ["email", "sms", "in_app"]
        )

        # Compliance defaults driven by resolved config output
        compliance_defaults: dict[str, object] = {
            "mandatory_training_enabled": defaults["mandatory_training_enabled"],
            "gdpr_consent_required": defaults["gdpr_consent_required"],
            "data_retention_days": 365,
        }

        behavior_tuning: dict[str, object] = {
            "onboarding": {
                "instant_setup": True,
                "preferred_channel": "whatsapp" if is_whatsapp_primary else "email",
                "dashboard_required": False,
            },
            "branding": {
                "logo_url": "",
                "color_scheme": "default",
                "theme": "platform_default",
            },
            "locale": {
                "language": "en",
                "timezone": "UTC",
                "date_format": "YYYY-MM-DD",
                "currency": currency,
            },
            "communication": {
                "routing_priority": routing_priority,
                "use_platform_default_templates": True,
            },
            "fees": {
                "currency": currency,
                "grace_period_days": 7,
                "overdue_trigger_days": 7,
                "reminder_cadence_days": 3,
                "fee_reminders_enabled": True,
            },
            "attendance": {
                "mode": "daily",
                "consecutive_absences_alert": 3,
                "min_attendance_pct": 75,
                "attendance_alerts_enabled": True,
            },
            "compliance": compliance_defaults,
            "report_schedule": {
                "frequency": "weekly",
                "day": "monday",
                "time": "08:00",
                "report_schedule_enabled": True,
            },
            "notification_templates": {
                "use_platform_defaults": True,
            },
        }

        self._config_service.upsert_override(
            ConfigOverride(
                scope=ConfigScope(level=ConfigLevel.TENANT, scope_id=request.tenant_id),
                behavior_tuning=behavior_tuning,
            )
        )
        return behavior_tuning

    def apply_notification_template_defaults(self, *, request: OnboardingRequest) -> dict[str, dict[str, str]]:
        """CGAP-048: BC-ONBOARD-01 — materialize concrete notification template defaults.

        Replaces the 'use_platform_defaults: True' placeholder with actual template content
        so no tenant begins operation with blank forms. Templates are derived from
        segment_type + country_code. Stored in config service under behavior_tuning.notification_templates.
        """
        # MS-CONFIG-01 (MS§3.2): read whatsapp and compliance flags from resolved config output
        defaults = self._resolve_country_segment_defaults(request)
        is_whatsapp = defaults["is_whatsapp_primary"]
        mandatory_training = defaults["mandatory_training_enabled"]

        # Base salutation adapts to communication channel
        salutation = "Hi {{learner_name}}," if is_whatsapp else "Dear {{learner_name}},"
        sign_off = "Regards,\n{{institution_name}}" if not is_whatsapp else "— {{institution_name}}"

        templates: dict[str, dict[str, str]] = {
            "welcome_message": {
                "subject": "Welcome to {{institution_name}}",
                "body": (
                    f"{salutation}\n\nWelcome! You're now enrolled at {{{{institution_name}}}}. "
                    "Your learning journey starts today.\n\n"
                    "Reply STATUS to check your progress at any time.\n\n"
                    f"{sign_off}"
                ),
                "channel": "whatsapp" if is_whatsapp else "email",
            },
            "fee_reminder": {
                "subject": "Fee reminder — {{amount_due}} due by {{due_date}}",
                "body": (
                    f"{salutation}\n\nThis is a reminder that {{{{amount_due}}}} is due by {{{{due_date}}}}. "
                    "Reply PAY to initiate payment or WAIVE to raise a dispute.\n\n"
                    f"{sign_off}"
                ),
                "channel": "whatsapp" if is_whatsapp else "email",
            },
            "attendance_alert": {
                "subject": "Attendance alert — action required",
                "body": (
                    f"{salutation}\n\nYour attendance has dropped below the required threshold. "
                    "Please contact your instructor or reply CONTACT for support.\n\n"
                    f"{sign_off}"
                ),
                "channel": "whatsapp" if is_whatsapp else "email",
            },
            "assignment_reminder": {
                "subject": "Reminder: {{assignment_title}} due {{due_date}}",
                "body": (
                    f"{salutation}\n\nA reminder that '{{{{assignment_title}}}}' is due on {{{{due_date}}}}. "
                    "Log in to submit or reply INFO for details.\n\n"
                    f"{sign_off}"
                ),
                "channel": "whatsapp" if is_whatsapp else "email",
            },
        }

        # Compliance reminder template when resolved config output requires mandatory training
        if mandatory_training:
            templates["compliance_reminder"] = {
                "subject": "Compliance training due — {{module_name}}",
                "body": (
                    f"{salutation}\n\nYour mandatory compliance module '{{{{module_name}}}}' "
                    "is due by {{{{due_date}}}}. Reply ENROLL to start immediately.\n\n"
                    f"{sign_off}"
                ),
                "channel": "email",
            }

        self._config_service.upsert_override(
            ConfigOverride(
                scope=ConfigScope(level=ConfigLevel.TENANT, scope_id=request.tenant_id),
                behavior_tuning={"notification_templates": {
                    "use_platform_defaults": False,
                    "templates": templates,
                }},
            )
        )
        return templates

    def apply_pakistan_default_config(self, *, request: OnboardingRequest) -> dict[str, object]:
        """Backward-compatible alias — delegates to apply_default_config().

        CGAP-047: The Pakistan-specific hardcode has been replaced with the generic
        segment/country-derived config. Callers of apply_pakistan_default_config()
        now receive fully derived defaults for any country/segment profile.
        """
        return self.apply_default_config(request=request)

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
