from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException

from backend.services.shared.models.tenant import TenantContract
from backend.services.shared.utils.capability_check import is_capability_enabled

from .schemas import (
    ConceptExplanationRequest,
    ContextualTutoringRequest,
    InteractionType,
    LearnerQuestionRequest,
    LearningGuidanceRequest,
    TutorResponse,
    TutorSessionSummary,
    AnalyticsTutorRequest,
)


@dataclass
class TutorSession:
    session_id: str
    tenant_id: str
    learner_id: str
    context: dict
    interactions: list[TutorResponse] = field(default_factory=list)


class AITutorService:
    def __init__(self) -> None:
        self._sessions: dict[str, TutorSession] = {}

    @staticmethod
    def _now() -> datetime:
        return datetime.now(timezone.utc)

    def explain_concept(self, request: ConceptExplanationRequest) -> TutorResponse:
        self._assert_capability(request.tenant_id, "ai.tutor")
        message = (
            f"{request.concept} can be understood as a practical tool for {request.learner_goal or 'solving the current lesson objective'}. "
            f"Start with the core definition, then relate it to your course {request.context.course_id}, and finish with one quick self-check question."
        )
        follow_up = [
            f"Summarize {request.concept} in your own words.",
            "Identify one real scenario where this concept applies.",
        ]
        resources = [
            f"course://{request.context.course_id}/concepts/{request.concept.lower().replace(' ', '-')}",
            f"course://{request.context.course_id}/practice/quick-check",
        ]
        return self._store_interaction(
            request.tenant_id,
            request.learner_id,
            request.context.model_dump(),
            InteractionType.EXPLANATION,
            message,
            follow_up,
            resources,
        )

    def answer_question(self, request: LearnerQuestionRequest) -> TutorResponse:
        self._assert_capability(request.tenant_id, "ai.tutor")
        message = (
            f"Answer: {request.question.strip('?')} relies on understanding {', '.join(request.context.struggling_topics) or 'the lesson prerequisites'}. "
            "Break the question into parts, verify assumptions, and test with a short example before committing to a final answer."
        )
        follow_up = [
            "Which part of this answer feels least clear?",
            "Try solving a similar question with one variable changed.",
        ]
        resources = [
            f"course://{request.context.course_id}/lesson/{request.context.lesson_id or 'overview'}",
        ]
        return self._store_interaction(
            request.tenant_id,
            request.learner_id,
            request.context.model_dump(),
            InteractionType.QUESTION,
            message,
            follow_up,
            resources,
        )

    def provide_contextual_tutoring(self, request: ContextualTutoringRequest) -> TutorResponse:
        self._assert_capability(request.tenant_id, "ai.tutor")
        message = (
            f"For {request.activity_type}, compare your submission against the expected outcome: {request.expected_outcome}. "
            "Focus first on correctness, then on clarity, and finally on efficiency."
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
            request.context.model_dump(),
            InteractionType.CONTEXTUAL_TUTORING,
            message,
            follow_up,
            resources,
        )

    def generate_guidance(self, request: LearningGuidanceRequest) -> TutorResponse:
        self._assert_capability(request.tenant_id, "ai.tutor")
        pace = "accelerated" if request.current_progress < 40 else "balanced"
        message = (
            f"Use a {pace} plan: reserve {request.time_available_minutes} minutes today for review, practice, and recap. "
            f"Current progress is {request.current_progress:.1f}%, so prioritize struggling topics before moving to new content."
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
            request.context.model_dump(),
            InteractionType.GUIDANCE,
            message,
            follow_up,
            resources,
        )

    def generate_analytics_guidance(self, request: AnalyticsTutorRequest) -> TutorResponse:
        self._assert_capability(request.tenant_id, "ai.tutor")
        risk_hint = "high" if request.completion_rate < 60 or request.average_sentiment < -0.2 else "moderate"
        message = (
            f"Analytics signal indicates {risk_hint} learner-risk with {request.completion_rate:.1f}% completion and "
            f"{request.trend_direction} engagement trend. Focus next tutoring turn on {request.suggested_focus}."
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
            request.context.model_dump(),
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

    def _tenant_contract(self, tenant_id: str) -> TenantContract:
        return TenantContract(tenant_id=tenant_id, name=tenant_id, country_code="US", segment_type="enterprise", plan_type="enterprise", addon_flags=["ai_tutor"]).normalized()

    def _assert_capability(self, tenant_id: str, capability: str) -> None:
        if not is_capability_enabled(self._tenant_contract(tenant_id), capability):
            raise HTTPException(status_code=403, detail=f"capability disabled: {capability}")

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
