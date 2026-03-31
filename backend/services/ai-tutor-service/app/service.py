from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol
from uuid import uuid4

import httpx
from fastapi import HTTPException

from shared.control_plane import ConfigService, EntitlementService
from shared.utils.entitlement import TenantEntitlementContext
from backend.services.shared.utils.tenant_context import tenant_contract_from_inputs

from .schemas import (
    AnalyticsTutorRequest,
    ConceptExplanationRequest,
    ContextualTutoringRequest,
    InteractionType,
    LearnerQuestionRequest,
    LearningGuidanceRequest,
    TutorResponse,
    TutorSessionSummary,
)


@dataclass
class TutorSession:
    session_id: str
    tenant_id: str
    learner_id: str
    context: dict
    interactions: list[TutorResponse] = field(default_factory=list)


@dataclass
class TutorContextBundle:
    course_data: dict[str, Any]
    progress_data: dict[str, Any]
    analytics_data: dict[str, Any]

    def course_title(self, fallback: str) -> str:
        return str(self.course_data.get("title") or fallback)

    def completion_percent(self, fallback: float | None = None) -> float | None:
        progress = self.progress_data.get("progress_percentage")
        if isinstance(progress, (int, float)):
            return float(progress)
        return fallback

    def engagement_trend(self, fallback: str = "stable") -> str:
        trend = self.analytics_data.get("trend_direction")
        if isinstance(trend, str) and trend:
            return trend
        return fallback


class LearningDataProvider(Protocol):
    def get_course(self, tenant_id: str, course_id: str) -> dict[str, Any]: ...

    def get_course_progress(self, tenant_id: str, learner_id: str, course_id: str) -> dict[str, Any]: ...

    def get_analytics(self, tenant_id: str, learner_id: str, course_id: str) -> dict[str, Any]: ...


class HTTPServiceDataProvider:
    def __init__(self, timeout_seconds: float = 2.0) -> None:
        self._course_base_url = os.getenv("COURSE_SERVICE_URL", "http://course-service:8000")
        self._progress_base_url = os.getenv("PROGRESS_SERVICE_URL", "http://progress-service:8000")
        self._analytics_base_url = os.getenv("ANALYTICS_SERVICE_URL", "http://learning-analytics-service:8000")
        self._service_token = os.getenv("AI_TUTOR_SERVICE_TOKEN")
        self._timeout = timeout_seconds

    def get_course(self, tenant_id: str, course_id: str) -> dict[str, Any]:
        payload = self._get_json(
            f"{self._course_base_url}/api/v1/courses/{course_id}",
            tenant_id=tenant_id,
        )
        if isinstance(payload.get("data"), dict):
            return payload["data"]
        return payload

    def get_course_progress(self, tenant_id: str, learner_id: str, course_id: str) -> dict[str, Any]:
        return self._get_json(
            (
                f"{self._progress_base_url}/api/v1/progress/learners/{learner_id}"
                f"/courses/{course_id}?tenant_id={tenant_id}"
            ),
            tenant_id=tenant_id,
        )

    def get_analytics(self, tenant_id: str, learner_id: str, course_id: str) -> dict[str, Any]:
        payload = self._get_json(
            f"{self._analytics_base_url}/api/v1/analytics/courses/{course_id}/engagement/dashboard?tenant_id={tenant_id}",
            tenant_id=tenant_id,
        )
        if "data" in payload and isinstance(payload["data"], dict):
            payload = payload["data"]
        signals = payload.get("signals") if isinstance(payload.get("signals"), dict) else {}
        if "trend_direction" not in signals:
            trend = payload.get("trend_direction") or payload.get("engagement_trend") or "stable"
            signals["trend_direction"] = trend
        if "learner_id" not in signals:
            signals["learner_id"] = learner_id
        return signals

    def _get_json(self, url: str, tenant_id: str) -> dict[str, Any]:
        headers = {"X-Tenant-Id": tenant_id}
        if self._service_token:
            headers["Authorization"] = f"Bearer {self._service_token}"

        try:
            response = httpx.get(url, headers=headers, timeout=self._timeout)
            response.raise_for_status()
        except httpx.HTTPError:
            return {}

        body = response.json()
        return body if isinstance(body, dict) else {}


class AITutorService:
    def __init__(self, data_provider: LearningDataProvider | None = None) -> None:
        self._sessions: dict[str, TutorSession] = {}
        self._data_provider = data_provider or HTTPServiceDataProvider()
        self._config_service = ConfigService()
        self._entitlement_service = EntitlementService(config_service=self._config_service)

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def explain_concept(self, request: ConceptExplanationRequest) -> TutorResponse:
        self._assert_capability(request.tenant_id, "ai.tutor")
        bundle = self._build_context_bundle(request.tenant_id, request.learner_id, request.context.course_id)
        message = (
            f"{request.concept} in {bundle.course_title(request.context.course_id)} is best learned as a practical tool for "
            f"{request.learner_goal or 'solving the current lesson objective'}. "
            f"Your current completion is {bundle.completion_percent(0.0) or 0.0:.1f}%, so start with the core definition, "
            "connect it to your current lesson, and close with one self-check question."
        )
        follow_up = [
            f"Summarize {request.concept} in your own words.",
            "Identify one real scenario where this concept applies.",
            f"Relate this concept to your current trend: {bundle.engagement_trend()}.",
        ]
        resources = [
            f"course://{request.context.course_id}/concepts/{request.concept.lower().replace(' ', '-')}",
            f"course://{request.context.course_id}/practice/quick-check",
        ]
        return self._store_interaction(
            request.tenant_id,
            request.learner_id,
            self._context_with_live_data(request.context.model_dump(), bundle),
            InteractionType.EXPLANATION,
            message,
            follow_up,
            resources,
        )

    def answer_question(self, request: LearnerQuestionRequest) -> TutorResponse:
        self._assert_capability(request.tenant_id, "ai.tutor")
        bundle = self._build_context_bundle(request.tenant_id, request.learner_id, request.context.course_id)
        message = (
            f"Answer: {request.question.strip('?')} for {bundle.course_title(request.context.course_id)} should account for "
            f"your struggling topics ({', '.join(request.context.struggling_topics) or 'lesson prerequisites'}) and "
            f"your progress state ({bundle.completion_percent(0.0) or 0.0:.1f}% complete). "
            "Break it into parts, verify assumptions, and test a short example before finalizing."
        )
        follow_up = [
            "Which part of this answer feels least clear?",
            "Try solving a similar question with one variable changed.",
            f"If engagement trend stays {bundle.engagement_trend()}, schedule one quick recap.",
        ]
        resources = [
            f"course://{request.context.course_id}/lesson/{request.context.lesson_id or 'overview'}",
        ]
        return self._store_interaction(
            request.tenant_id,
            request.learner_id,
            self._context_with_live_data(request.context.model_dump(), bundle),
            InteractionType.QUESTION,
            message,
            follow_up,
            resources,
        )

    def provide_contextual_tutoring(self, request: ContextualTutoringRequest) -> TutorResponse:
        self._assert_capability(request.tenant_id, "ai.tutor")
        bundle = self._build_context_bundle(request.tenant_id, request.learner_id, request.context.course_id)
        message = (
            f"For {request.activity_type} in {bundle.course_title(request.context.course_id)}, compare your submission "
            f"against the expected outcome: {request.expected_outcome}. "
            f"Given {bundle.completion_percent(0.0) or 0.0:.1f}% completion and {bundle.engagement_trend()} engagement trend, "
            "focus first on correctness, then clarity, then efficiency."
        )
        follow_up = [
            "Mark one step in your submission that can be simplified.",
            "Re-attempt the task using the expected outcome as a checklist.",
        ]
        resources = [
            f"course://{request.context.course_id}/activities/{request.activity_type}",
            "course://study-skills/error-analysis",
        ]
        return self._store_interaction(
            request.tenant_id,
            request.learner_id,
            self._context_with_live_data(request.context.model_dump(), bundle),
            InteractionType.CONTEXTUAL_TUTORING,
            message,
            follow_up,
            resources,
        )

    def generate_guidance(self, request: LearningGuidanceRequest) -> TutorResponse:
        self._assert_capability(request.tenant_id, "ai.tutor")
        bundle = self._build_context_bundle(request.tenant_id, request.learner_id, request.context.course_id)
        completion = bundle.completion_percent(request.current_progress) or request.current_progress
        pace = "accelerated" if completion < 40 else "balanced"
        message = (
            f"Use a {pace} plan for {bundle.course_title(request.context.course_id)}: reserve {request.time_available_minutes} minutes today "
            "for review, practice, and recap. "
            f"Live progress is {completion:.1f}% with a {bundle.engagement_trend()} engagement trend, "
            "so prioritize struggling topics before new content."
        )
        follow_up = [
            "Set a 10-minute checkpoint and verify one completed objective.",
            "End the session by listing two unresolved questions.",
        ]
        resources = [
            f"course://{request.context.course_id}/roadmap",
            "course://learning-path/recommended-next-steps",
        ]
        return self._store_interaction(
            request.tenant_id,
            request.learner_id,
            self._context_with_live_data(request.context.model_dump(), bundle),
            InteractionType.GUIDANCE,
            message,
            follow_up,
            resources,
        )

    def generate_analytics_guidance(self, request: AnalyticsTutorRequest) -> TutorResponse:
        self._assert_capability(request.tenant_id, "ai.tutor")
        bundle = self._build_context_bundle(request.tenant_id, request.learner_id, request.context.course_id)
        completion_rate = bundle.completion_percent(request.completion_rate) or request.completion_rate
        trend_direction = bundle.engagement_trend(request.trend_direction)
        risk_hint = "high" if completion_rate < 60 or request.average_sentiment < -0.2 else "moderate"
        message = (
            f"Analytics indicates {risk_hint} learner-risk in {bundle.course_title(request.context.course_id)} with "
            f"{completion_rate:.1f}% completion and {trend_direction} engagement trend. "
            f"Focus next tutoring turn on {request.suggested_focus}."
        )
        follow_up = [
            "Review the last missed concept and explain it back in one sentence.",
            "Complete one short practice item before moving to new material.",
        ]
        resources = [
            f"course://{request.context.course_id}/interventions/{request.suggested_focus}",
            "course://learning-support/at-risk-playbook",
        ]
        return self._store_interaction(
            request.tenant_id,
            request.learner_id,
            self._context_with_live_data(request.context.model_dump(), bundle),
            InteractionType.GUIDANCE,
            message,
            follow_up,
            resources,
        )

    def get_session_summary(self, tenant_id: str, session_id: str) -> TutorSessionSummary:
        session = self._sessions.get(session_id)
        if not session or session.tenant_id != tenant_id:
            raise HTTPException(status_code=404, detail="Tutor session not found for tenant")

        return TutorSessionSummary(
            session_id=session.session_id,
            tenant_id=session.tenant_id,
            learner_id=session.learner_id,
            context=session.context,
            interactions=session.interactions,
        )

    def _tenant_context(self, tenant_id: str) -> TenantEntitlementContext:
        tenant = tenant_contract_from_inputs(tenant_id=tenant_id)
        return TenantEntitlementContext(
            tenant_id=tenant.tenant_id,
            country_code=tenant.country_code,
            segment_id=tenant.segment_type,
            plan_type=tenant.plan_type,
            add_ons=tuple(tenant.addon_flags),
        )

    def _assert_capability(self, tenant_id: str, capability: str) -> None:
        if not self._entitlement_service.is_enabled(self._tenant_context(tenant_id), capability):
            raise HTTPException(status_code=403, detail=f"capability disabled: {capability}")

    def _build_context_bundle(self, tenant_id: str, learner_id: str, course_id: str) -> TutorContextBundle:
        return TutorContextBundle(
            course_data=self._data_provider.get_course(tenant_id=tenant_id, course_id=course_id),
            progress_data=self._data_provider.get_course_progress(
                tenant_id=tenant_id,
                learner_id=learner_id,
                course_id=course_id,
            ),
            analytics_data=self._data_provider.get_analytics(
                tenant_id=tenant_id,
                learner_id=learner_id,
                course_id=course_id,
            ),
        )

    @staticmethod
    def _context_with_live_data(context: dict[str, Any], bundle: TutorContextBundle) -> dict[str, Any]:
        return {
            **context,
            "course_data": bundle.course_data,
            "progress_data": bundle.progress_data,
            "analytics_data": bundle.analytics_data,
        }

    def _store_interaction(
        self,
        tenant_id: str,
        learner_id: str,
        context: dict,
        interaction_type: InteractionType,
        message: str,
        follow_up_actions: list[str],
        recommended_resources: list[str],
    ) -> TutorResponse:
        session_id = self._find_or_create_session(tenant_id, learner_id, context)
        interaction = TutorResponse(
            session_id=session_id,
            interaction_id=str(uuid4()),
            interaction_type=interaction_type,
            message=message,
            follow_up_actions=follow_up_actions,
            recommended_resources=recommended_resources,
            created_at=self._now(),
        )
        self._sessions[session_id].interactions.append(interaction)
        self._sessions[session_id].context = context
        return interaction

    def _find_or_create_session(self, tenant_id: str, learner_id: str, context: dict) -> str:
        for existing_id, session in self._sessions.items():
            if session.tenant_id == tenant_id and session.learner_id == learner_id:
                return existing_id

        session_id = str(uuid4())
        self._sessions[session_id] = TutorSession(
            session_id=session_id,
            tenant_id=tenant_id,
            learner_id=learner_id,
            context=context,
        )
        return session_id
