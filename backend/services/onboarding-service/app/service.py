from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .models import ONBOARDING_STEPS, OnboardingSession, SmartDefault


class OnboardingService:
    def __init__(self) -> None:
        self._sessions: Dict[str, OnboardingSession] = {}
        self._by_tenant: Dict[str, str] = {}

    def start_onboarding(self, body: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
        tenant_id = body.get("tenant_id", "")
        if tenant_id in self._by_tenant:
            session = self._sessions[self._by_tenant[tenant_id]]
            return 200, {"session_id": session.session_id, "status": session.status,
                         "current_step": ONBOARDING_STEPS[session.current_step],
                         "message": "onboarding_already_started"}

        session = OnboardingSession(
            session_id=f"onboard-{secrets.token_urlsafe(8)}",
            tenant_id=tenant_id,
            segment_type=body.get("segment_type", "corp"),
            plan_type=body.get("plan_type", "basic"),
            country_code=body.get("country_code", "US"),
            steps=list(ONBOARDING_STEPS),
        )
        # Auto-complete first two steps (system-driven)
        session.completed_steps = ["tenant_record_created", "profile_detected"]
        session.current_step = 2
        self._sessions[session.session_id] = session
        self._by_tenant[tenant_id] = session.session_id
        return 201, self._serialize(session)

    def complete_step(self, session_id: str, step_name: str, data: Dict[str, Any] = None) -> Tuple[int, Dict[str, Any]]:
        session = self._sessions.get(session_id)
        if not session:
            return 404, {"error": "session_not_found"}
        if session.status == "completed":
            return 409, {"error": "onboarding_already_complete"}

        expected = session.steps[session.current_step] if session.current_step < len(session.steps) else None
        if expected and step_name != expected:
            return 422, {"error": "wrong_step", "expected": expected, "provided": step_name}

        session.completed_steps.append(step_name)
        if data:
            session.wizard_data.update(data)
        session.current_step += 1

        if session.current_step >= len(session.steps):
            session.status = "completed"
            session.completed_at = datetime.now(timezone.utc)

        return 200, self._serialize(session)

    def get_status(self, session_id: str) -> Tuple[int, Dict[str, Any]]:
        session = self._sessions.get(session_id)
        if not session:
            return 404, {"error": "session_not_found"}
        return 200, self._serialize(session)

    def get_defaults(self, segment_type: str, plan_type: str, country_code: str) -> Tuple[int, Dict[str, Any]]:
        # BC-ONBOARD-01: every option has a sensible pre-filled default
        defaults = [
            SmartDefault("branding", {"theme": "platform-default", "logo": None}, "platform"),
            SmartDefault("locale", _infer_locale(country_code), f"country:{country_code}"),
            SmartDefault("feature_flags", f"{segment_type}_{plan_type}_bundle", "capability-registry"),
            SmartDefault("notification_templates", "platform-default-templates", "platform"),
            SmartDefault("automation_workflows", "default-on-all", "workflow-engine"),
            SmartDefault("fee_reminder_schedule", {"trigger_days_overdue": 7}, "platform"),
            SmartDefault("attendance_rules", {"consecutive_absences_threshold": 3}, "platform"),
            SmartDefault("compliance_settings", _compliance_defaults(segment_type), f"segment:{segment_type}"),
            SmartDefault("report_schedule", {"day": "Monday", "time": "08:00"}, "platform"),
        ]
        return 200, {
            "segment_type": segment_type, "plan_type": plan_type, "country_code": country_code,
            "defaults": [{"area": d.area, "default_value": d.default_value,
                           "source": d.source, "customisable": d.customisable} for d in defaults],
        }

    def _serialize(self, s: OnboardingSession) -> Dict[str, Any]:
        current_step_name = s.steps[s.current_step] if s.current_step < len(s.steps) else "done"
        return {
            "session_id": s.session_id, "tenant_id": s.tenant_id,
            "status": s.status, "current_step": current_step_name,
            "current_step_index": s.current_step,
            "completed_steps": s.completed_steps,
            "total_steps": len(s.steps),
            "progress_pct": round(len(s.completed_steps) / len(s.steps) * 100),
            "wizard_data": s.wizard_data,
        }


def _infer_locale(country_code: str) -> str:
    return {"PK": "ur-PK", "IN": "hi-IN", "US": "en-US", "GB": "en-GB"}.get(country_code, "en-US")


def _compliance_defaults(segment_type: str) -> Dict[str, str]:
    return {"school": "enhanced", "corp": "baseline", "enterprise": "strict"}.get(segment_type, {"level": "baseline"})
