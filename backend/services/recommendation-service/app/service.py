from __future__ import annotations

from collections import defaultdict

from backend.services.shared.models.tenant import TenantContract
from backend.services.shared.utils.capability_check import is_capability_enabled

from .models import (
    BehavioralLearningRecommendation,
    LearnerRecommendationBundle,
    LearningPathSuggestion,
    PersonalizedCourseRecommendation,
    RecommendationRationale,
    SkillGapRecommendation,
)
from .schemas import (
    BehavioralRecommendationRequest,
    LearningPathSuggestionRequest,
    PersonalizedRecommendationRequest,
    SkillGapRecommendationRequest,
    AnalyticsRecommendationRequest,
)


class RecommendationService:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, LearnerRecommendationBundle]] = defaultdict(dict)

    def generate_personalized_courses(
        self, req: PersonalizedRecommendationRequest
    ) -> list[PersonalizedCourseRecommendation]:
        self._assert_capability(req.tenant_id, "recommendation.basic")
        modalities = req.preferred_modalities or ["self-paced"]
        skills = req.target_skills or ["general-upskilling"]
        base_score = min(1.0, 0.45 + (req.available_minutes_per_week / 600))

        items = [
            PersonalizedCourseRecommendation(
                tenant_id=req.tenant_id,
                learner_id=req.learner_id,
                course_id=f"course-{skill}-{index + 1}",
                score=max(0.1, base_score - (index * 0.08)),
                estimated_minutes=max(30, req.available_minutes_per_week // (index + 2)),
                difficulty_tier="intermediate" if req.available_minutes_per_week > 180 else "foundation",
                rationale=RecommendationRationale(
                    tags=["skill-alignment", f"modality:{modalities[index % len(modalities)]}"],
                    explanation=f"Selected for target skill '{skill}' using preference-aware ranking.",
                ),
            )
            for index, skill in enumerate(skills[:5])
        ]
        self._upsert(req.tenant_id, req.learner_id, personalized_courses=items)
        return items

    def generate_skill_gap_recommendations(
        self, req: SkillGapRecommendationRequest
    ) -> list[SkillGapRecommendation]:
        self._assert_capability(req.tenant_id, "recommendation.basic")
        recommendations: list[SkillGapRecommendation] = []
        for skill in req.required_skills:
            current = req.current_skill_levels.get(skill, 0.0)
            target = req.target_skill_levels.get(skill, 0.8)
            gap = max(0.0, target - current)
            severity = "critical" if gap >= 0.5 else "moderate" if gap >= 0.25 else "minor"

            recommendations.append(
                SkillGapRecommendation(
                    tenant_id=req.tenant_id,
                    learner_id=req.learner_id,
                    skill_id=skill,
                    current_level=current,
                    target_level=target,
                    severity=severity,
                    score=min(1.0, gap + 0.2),
                    interventions=[
                        f"course-bridge-{skill}",
                        f"project-practice-{skill}",
                        f"coaching-session-{skill}",
                    ],
                    rationale=RecommendationRationale(
                        tags=["skill-gap", f"severity:{severity}"],
                        explanation="Gap priority calculated from target-current proficiency deltas.",
                    ),
                )
            )

        recommendations.sort(key=lambda item: item.score, reverse=True)
        self._upsert(req.tenant_id, req.learner_id, skill_gaps=recommendations)
        return recommendations

    def generate_learning_path_suggestions(
        self, req: LearningPathSuggestionRequest
    ) -> list[LearningPathSuggestion]:
        self._assert_capability(req.tenant_id, "recommendation.basic")
        tracks = ["core", "accelerated", "project-based"]
        suggestions: list[LearningPathSuggestion] = []
        for index, track in enumerate(tracks):
            ordered = [*req.mandatory_course_ids, f"elective-{track}-1", f"elective-{track}-2"]
            suggestions.append(
                LearningPathSuggestion(
                    tenant_id=req.tenant_id,
                    learner_id=req.learner_id,
                    learning_path_id=f"path-{req.goal.replace(' ', '-').lower()}-{track}",
                    ordered_course_ids=ordered,
                    estimated_completion_days=max(7, int((len(ordered) * 3) / max(1, req.available_hours_per_week))),
                    score=max(0.2, 0.9 - (index * 0.12)),
                    rationale=RecommendationRationale(
                        tags=["path-optimization", f"goal:{req.goal}", f"track:{track}"],
                        explanation="Sequenced with prerequisite-safe ordering and learner time budget.",
                    ),
                )
            )

        self._upsert(req.tenant_id, req.learner_id, learning_paths=suggestions)
        return suggestions

    def generate_behavioral_recommendations(
        self, req: BehavioralRecommendationRequest
    ) -> list[BehavioralLearningRecommendation]:
        self._assert_capability(req.tenant_id, "recommendation.basic")
        recommendations: list[BehavioralLearningRecommendation] = []

        if req.dropoff_rate > 0.4:
            recommendations.append(
                BehavioralLearningRecommendation(
                    tenant_id=req.tenant_id,
                    learner_id=req.learner_id,
                    behavior_signal="high_dropoff",
                    action="assign_microlearning",
                    habit_goal="Complete one 10-minute lesson daily for 14 days",
                    score=min(1.0, req.dropoff_rate + 0.2),
                    rationale=RecommendationRationale(
                        tags=["behavioral", "re-engagement"],
                        explanation="Short-form content suggested to reduce abandonment and rebuild momentum.",
                    ),
                )
            )

        if req.activity_streak_days < 3:
            recommendations.append(
                BehavioralLearningRecommendation(
                    tenant_id=req.tenant_id,
                    learner_id=req.learner_id,
                    behavior_signal="low_streak",
                    action="enable_streak_nudges",
                    habit_goal="Reach a 5-day learning streak",
                    score=0.72,
                    rationale=RecommendationRationale(
                        tags=["behavioral", "habit-formation"],
                        explanation="Streak nudges and reminders improve consistency for low-frequency learners.",
                    ),
                )
            )

        if req.average_session_minutes < 15:
            recommendations.append(
                BehavioralLearningRecommendation(
                    tenant_id=req.tenant_id,
                    learner_id=req.learner_id,
                    behavior_signal="short_sessions",
                    action="suggest_focus_blocks",
                    habit_goal="Increase average study session to 20 minutes",
                    score=0.64,
                    rationale=RecommendationRationale(
                        tags=["behavioral", "focus-time"],
                        explanation="Focus blocks and milestone prompts support deeper practice sessions.",
                    ),
                )
            )

        self._upsert(req.tenant_id, req.learner_id, behavioral=recommendations)
        return recommendations

    def generate_from_analytics(self, req: AnalyticsRecommendationRequest) -> list[BehavioralLearningRecommendation]:
        self._assert_capability(req.tenant_id, "recommendation.basic")
        dropoff_rate = max(0.0, 1 - (req.completion_rate / 100))
        streak_days = 1 if req.trend_direction == "down" else 4
        avg_minutes = 10 if req.engagement_score < 40 else 22
        behavior_req = BehavioralRecommendationRequest(
            tenant_id=req.tenant_id,
            learner_id=req.learner_id,
            activity_streak_days=streak_days,
            average_session_minutes=avg_minutes,
            dropoff_rate=round(dropoff_rate, 2),
        )
        return self.generate_behavioral_recommendations(behavior_req)

    def get_bundle(self, tenant_id: str, learner_id: str) -> LearnerRecommendationBundle:
        return self._store.get(tenant_id, {}).get(learner_id, LearnerRecommendationBundle(learner_id=learner_id))

    def _tenant_contract(self, tenant_id: str) -> TenantContract:
        return TenantContract(tenant_id=tenant_id, name=tenant_id, country_code="US", segment_type="enterprise", plan_type="pro", addon_flags=[]).normalized()

    def _assert_capability(self, tenant_id: str, capability: str) -> None:
        if not is_capability_enabled(self._tenant_contract(tenant_id), capability):
            raise ValueError(f"capability disabled: {capability}")

    def _upsert(
        self,
        tenant_id: str,
        learner_id: str,
        personalized_courses: list[PersonalizedCourseRecommendation] | None = None,
        skill_gaps: list[SkillGapRecommendation] | None = None,
        learning_paths: list[LearningPathSuggestion] | None = None,
        behavioral: list[BehavioralLearningRecommendation] | None = None,
    ) -> None:
        bundle = self._store[tenant_id].get(learner_id, LearnerRecommendationBundle(learner_id=learner_id))
        if personalized_courses is not None:
            bundle.personalized_courses = personalized_courses
        if skill_gaps is not None:
            bundle.skill_gaps = skill_gaps
        if learning_paths is not None:
            bundle.learning_paths = learning_paths
        if behavioral is not None:
            bundle.behavioral = behavioral
        self._store[tenant_id][learner_id] = bundle
