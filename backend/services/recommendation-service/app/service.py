from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from shared.control_plane import build_control_plane_client
from shared.utils.entitlement import TenantEntitlementContext
from backend.services.shared.utils.tenant_context import tenant_contract_from_inputs

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
    IntegratedRecommendationRequest,
)


class RecommendationService:
    def __init__(self) -> None:
        self._store: dict[str, dict[str, LearnerRecommendationBundle]] = defaultdict(dict)
        self._control_plane = build_control_plane_client()

    def generate_personalized_courses(
        self, req: PersonalizedRecommendationRequest
    ) -> list[PersonalizedCourseRecommendation]:
        self._assert_capability(req.tenant_id, "recommendation.basic")
        modalities = req.preferred_modalities or ["self-paced"]
        skills = req.target_skills or [f"{modalities[0]}-fluency"]
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
        pace_track = "accelerated" if req.available_hours_per_week >= 8 else "steady"
        depth_track = "deep-practice" if len(req.mandatory_course_ids) <= 2 else "coverage"
        tracks = [pace_track, depth_track]
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

    def generate_integrated_recommendations(
        self, req: IntegratedRecommendationRequest
    ) -> tuple[list[PersonalizedCourseRecommendation], list[LearningPathSuggestion]]:
        self._assert_capability(req.tenant_id, "recommendation.basic")
        inferred_by_skill = {row.skill_id: row for row in req.skill_inference}
        candidate_skills = set(req.target_skills) | set(inferred_by_skill)
        if not candidate_skills:
            candidate_skills = {f"{req.goal.lower().replace(' ', '-')}-foundation"}

        completed_or_active = set(req.progress.completed_course_ids) | set(req.progress.in_progress_course_ids)
        max_courses = min(6, max(2, len(candidate_skills)))
        ranked_skills = sorted(
            candidate_skills,
            key=lambda skill: self._skill_priority(skill, inferred_by_skill.get(skill)),
            reverse=True,
        )[:max_courses]

        hours_budget = req.available_hours_per_week * 60
        engagement_factor = req.analytics.average_engagement_score / 100
        completion_factor = req.analytics.completion_rate / 100
        trend_boost = 0.07 if req.analytics.trend_direction == "up" else -0.08 if req.analytics.trend_direction == "down" else 0.0

        personalized: list[PersonalizedCourseRecommendation] = []
        goal_slug = req.goal.lower().replace(" ", "-")
        for index, skill in enumerate(ranked_skills):
            signal = inferred_by_skill.get(skill)
            inferred_level = signal.inferred_level if signal else 0.0
            confidence = signal.confidence if signal else 0.35
            gap = max(0.0, 0.85 - inferred_level)
            tier = "advanced" if inferred_level >= 0.7 else "intermediate" if inferred_level >= 0.4 else "foundation"
            course_id = f"course-{goal_slug}-{skill.lower().replace(' ', '-')}-{tier}-{index + 1}"
            if course_id in completed_or_active:
                continue
            score = min(1.0, max(0.15, 0.42 + (0.45 * gap) + (0.2 * confidence) + trend_boost - (0.12 * completion_factor)))
            estimated = max(45, int((hours_budget * (0.8 + (0.4 * gap))) / max(1, len(ranked_skills))))
            personalized.append(
                PersonalizedCourseRecommendation(
                    tenant_id=req.tenant_id,
                    learner_id=req.learner_id,
                    course_id=course_id,
                    score=round(score, 3),
                    estimated_minutes=estimated,
                    difficulty_tier=tier,
                    rationale=RecommendationRationale(
                        tags=[
                            f"skill:{skill}",
                            f"analytics:engagement:{round(req.analytics.average_engagement_score, 1)}",
                            f"progress:path_completion:{round(req.progress.learning_path_completion_rate, 1)}",
                        ],
                        explanation=f"Prioritized from skill inference gap ({round(gap, 2)}) and learner analytics/progress signals.",
                    ),
                )
            )

        personalized.sort(key=lambda row: row.score, reverse=True)
        selected_course_ids = [row.course_id for row in personalized]
        learning_paths = self._build_learning_paths(req, selected_course_ids, engagement_factor)
        self._upsert(req.tenant_id, req.learner_id, personalized_courses=personalized, learning_paths=learning_paths)
        return personalized, learning_paths

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
        if not self._control_plane.is_enabled(self._tenant_context(tenant_id), capability):
            raise ValueError(f"capability disabled: {capability}")

    @staticmethod
    def _skill_priority(skill: str, signal: object | None) -> float:
        if not signal:
            return 0.5 + (0.02 * len(skill))
        inferred_level = getattr(signal, "inferred_level", 0.0)
        confidence = getattr(signal, "confidence", 0.0)
        return (1.0 - inferred_level) * 0.8 + (confidence * 0.2)

    def _build_learning_paths(
        self,
        req: IntegratedRecommendationRequest,
        selected_course_ids: Iterable[str],
        engagement_factor: float,
    ) -> list[LearningPathSuggestion]:
        selected = [course_id for course_id in selected_course_ids if course_id not in req.progress.completed_course_ids]
        baseline = [*req.mandatory_course_ids, *selected]
        if not baseline:
            baseline = [f"course-{req.goal.lower().replace(' ', '-')}-starter"]
        deduped = list(dict.fromkeys(baseline))

        pace_variant = "accelerated" if req.progress.weekly_active_minutes >= 180 and engagement_factor >= 0.55 else "steady"
        support_variant = "checkpoint-heavy" if req.analytics.trend_direction == "down" else "project-heavy"
        variants = [pace_variant, support_variant]
        suggestions: list[LearningPathSuggestion] = []
        for index, variant in enumerate(variants):
            if variant == "accelerated":
                ordered = deduped
            elif variant == "checkpoint-heavy":
                midpoint = max(1, len(deduped) // 2)
                ordered = deduped[:midpoint] + [f"checkpoint-{req.goal.lower().replace(' ', '-')}-{midpoint}"] + deduped[midpoint:]
            else:
                ordered = deduped + [f"project-{req.goal.lower().replace(' ', '-')}-{len(deduped)}"]
            estimated_days = max(7, int((len(ordered) * 2.5) / max(1, req.available_hours_per_week)))
            score = min(1.0, max(0.2, 0.86 - (0.14 * index) + (0.1 * (req.progress.learning_path_completion_rate / 100))))
            suggestions.append(
                LearningPathSuggestion(
                    tenant_id=req.tenant_id,
                    learner_id=req.learner_id,
                    learning_path_id=f"path-{req.goal.lower().replace(' ', '-')}-{variant}",
                    ordered_course_ids=ordered,
                    estimated_completion_days=estimated_days,
                    score=round(score, 3),
                    rationale=RecommendationRationale(
                        tags=[f"variant:{variant}", f"trend:{req.analytics.trend_direction}", "integrated-signals"],
                        explanation="Built from analytics trend, inferred skill gaps, and current completion momentum.",
                    ),
                )
            )
        return suggestions

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
