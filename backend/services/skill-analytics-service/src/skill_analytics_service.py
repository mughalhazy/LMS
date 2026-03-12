from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timedelta
from statistics import fmean
from typing import Dict, List, Optional

from .entities import (
    LearnerSkillAnalyticsAggregate,
    RoleSkillRequirement,
    Skill,
    UserSkill,
    UserSkillEvidence,
)


class SkillAnalyticsService:
    """Tenant-scoped skill analytics service for progression, gaps, mastery, and trends."""

    GAP_SEVERITY = ((2.0, "critical"), (1.0, "moderate"), (0.01, "minor"))

    def __init__(self) -> None:
        self._tenant_learner_data: Dict[str, Dict[str, LearnerSkillAnalyticsAggregate]] = {}
        self._tenant_skills: Dict[str, Dict[str, Skill]] = {}
        self._tenant_role_requirements: Dict[str, Dict[str, List[RoleSkillRequirement]]] = {}
        self._tenant_interventions: Dict[str, Dict[str, List[str]]] = {}

    def _get_or_create_aggregate(self, tenant_id: str, learner_id: str) -> LearnerSkillAnalyticsAggregate:
        tenant_bucket = self._tenant_learner_data.setdefault(tenant_id, {})
        if learner_id not in tenant_bucket:
            tenant_bucket[learner_id] = LearnerSkillAnalyticsAggregate(
                tenant_id=tenant_id,
                learner_id=learner_id,
            )
        return tenant_bucket[learner_id]

    def register_skill(self, tenant_id: str, skill_id: str, name: str, difficulty_base: float = 0.0) -> Skill:
        skill = Skill(skill_id=skill_id, name=name, difficulty_base=difficulty_base)
        self._tenant_skills.setdefault(tenant_id, {})[skill_id] = skill
        return skill

    def set_interventions(self, tenant_id: str, skill_id: str, interventions: List[str]) -> None:
        self._tenant_interventions.setdefault(tenant_id, {})[skill_id] = interventions

    def set_role_requirements(
        self,
        tenant_id: str,
        role_profile_id: str,
        requirements: List[RoleSkillRequirement],
    ) -> None:
        self._tenant_role_requirements.setdefault(tenant_id, {})[role_profile_id] = requirements

    def record_evidence(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        skill_id: str,
        evidence_type: str,
        normalized_score: float,
        evidence_date: Optional[datetime] = None,
        verified: bool = False,
        difficulty_weight: float = 1.0,
    ) -> UserSkillEvidence:
        aggregate = self._get_or_create_aggregate(tenant_id, learner_id)
        observed_at = evidence_date or datetime.utcnow()
        evidence = UserSkillEvidence(
            tenant_id=tenant_id,
            learner_id=learner_id,
            skill_id=skill_id,
            evidence_type=evidence_type,
            normalized_score=max(0.0, min(1.0, normalized_score)),
            evidence_date=observed_at,
            verified=verified,
            difficulty_weight=max(0.2, difficulty_weight),
        )
        aggregate.evidence_by_skill.setdefault(skill_id, []).append(evidence)

        skill_state = aggregate.skills.setdefault(
            skill_id,
            UserSkill(
                tenant_id=tenant_id,
                learner_id=learner_id,
                skill_id=skill_id,
            ),
        )
        skill_state.current_level = round(self._compute_current_proficiency(aggregate, skill_id), 4)
        skill_state.confidence = self._confidence_for_skill(aggregate, skill_id)
        skill_state.last_assessed_at = observed_at

        aggregate.trend_snapshots.setdefault(skill_id, []).append((observed_at, skill_state.current_level))
        aggregate.trend_snapshots[skill_id].sort(key=lambda item: item[0])
        return evidence

    def _compute_current_proficiency(self, aggregate: LearnerSkillAnalyticsAggregate, skill_id: str) -> float:
        evidence_list = aggregate.evidence_by_skill.get(skill_id, [])
        if not evidence_list:
            return 0.0

        now = datetime.utcnow()
        weighted_sum = 0.0
        total_weight = 0.0
        for item in evidence_list:
            recency_days = max((now - item.evidence_date).days, 0)
            recency_weight = max(0.2, 1 - (recency_days / 365))
            weight = recency_weight * item.difficulty_weight
            weighted_sum += item.normalized_score * 5.0 * weight
            total_weight += weight

        return weighted_sum / total_weight if total_weight else 0.0

    def _confidence_for_skill(self, aggregate: LearnerSkillAnalyticsAggregate, skill_id: str) -> float:
        evidence_list = aggregate.evidence_by_skill.get(skill_id, [])
        if not evidence_list:
            return 0.0
        count_factor = min(1.0, len(evidence_list) / 10)
        verification_factor = sum(1 for e in evidence_list if e.verified) / len(evidence_list)
        return round((count_factor * 0.7) + (verification_factor * 0.3), 4)

    def progression_metrics(
        self,
        tenant_id: str,
        learner_id: str,
        skill_id: str,
        target_level: float,
        time_window_days: int = 30,
    ) -> Dict[str, float]:
        aggregate = self._get_or_create_aggregate(tenant_id, learner_id)
        evidence = sorted(aggregate.evidence_by_skill.get(skill_id, []), key=lambda item: item.evidence_date)
        if not evidence:
            return {
                "baseline_proficiency": 0.0,
                "current_proficiency": 0.0,
                "absolute_change": 0.0,
                "velocity": 0.0,
                "milestone_attainment": 0.0,
            }

        baseline = evidence[0].normalized_score * 5.0
        current = aggregate.skills.get(skill_id, UserSkill(tenant_id, learner_id, skill_id)).current_level
        absolute_change = current - baseline

        window_start = datetime.utcnow() - timedelta(days=time_window_days)
        recent = [item for item in evidence if item.evidence_date >= window_start]
        if recent:
            velocity = ((recent[-1].normalized_score * 5.0) - (recent[0].normalized_score * 5.0)) / max(
                time_window_days,
                1,
            )
        else:
            velocity = 0.0

        milestone = 0.0 if target_level <= 0 else max(0.0, min(100.0, (current / target_level) * 100))
        return {
            "baseline_proficiency": round(baseline, 4),
            "current_proficiency": round(current, 4),
            "absolute_change": round(absolute_change, 4),
            "velocity": round(velocity, 4),
            "milestone_attainment": round(milestone, 2),
        }

    def detect_skill_gaps(
        self,
        tenant_id: str,
        learner_id: str,
        role_profile_id: str,
        urgency_factor: float = 1.0,
    ) -> List[Dict[str, object]]:
        aggregate = self._get_or_create_aggregate(tenant_id, learner_id)
        requirements = self._tenant_role_requirements.get(tenant_id, {}).get(role_profile_id, [])
        ranked_gaps: List[Dict[str, object]] = []

        for req in requirements:
            current = aggregate.skills.get(req.skill_id, UserSkill(tenant_id, learner_id, req.skill_id)).current_level
            gap = max(0.0, req.target_level - current)

            severity = "none"
            for threshold, label in self.GAP_SEVERITY:
                if gap >= threshold:
                    severity = label
                    break

            priority = gap * req.business_criticality * req.role_weight * max(urgency_factor, 0.1)
            interventions = self._tenant_interventions.get(tenant_id, {}).get(
                req.skill_id,
                ["assign_targeted_course", "schedule_coaching_session", "add_project_rotation"],
            )
            ranked_gaps.append(
                {
                    "role_profile_id": role_profile_id,
                    "skill_id": req.skill_id,
                    "target_level": req.target_level,
                    "current_level": round(current, 4),
                    "gap": round(gap, 4),
                    "severity": severity,
                    "priority": round(priority, 4),
                    "recommended_interventions": interventions,
                }
            )

        ranked_gaps.sort(key=lambda item: item["priority"], reverse=True)
        return ranked_gaps

    def mastery_scoring(
        self,
        tenant_id: str,
        learner_id: str,
        skill_id: str,
        w_assessment: float = 0.35,
        w_practice: float = 0.25,
        w_validation: float = 0.2,
        w_retention: float = 0.2,
    ) -> Dict[str, float | str]:
        aggregate = self._get_or_create_aggregate(tenant_id, learner_id)
        evidence = aggregate.evidence_by_skill.get(skill_id, [])
        if not evidence:
            return {
                "mastery_score": 0.0,
                "confidence_adjusted_score": 0.0,
                "mastery_band": "novice",
                "confidence": 0.0,
            }

        assessment = [e.normalized_score for e in evidence if e.evidence_type == "assessment"]
        practice = [e.normalized_score for e in evidence if e.evidence_type in {"project", "practice"}]
        validation = [e.normalized_score for e in evidence if e.evidence_type in {"peer_review", "manager_validation"}]

        assessment_score = fmean(assessment) if assessment else 0.0
        practice_score = fmean(practice) if practice else 0.0
        validation_score = fmean(validation) if validation else 0.0

        latest = max(e.evidence_date for e in evidence)
        days_since_latest = max((datetime.utcnow() - latest).days, 0)
        retention_score = max(0.0, 1 - (days_since_latest / 180))

        mastery = (
            (w_assessment * assessment_score)
            + (w_practice * practice_score)
            + (w_validation * validation_score)
            + (w_retention * retention_score)
        )

        confidence = self._confidence_for_skill(aggregate, skill_id)
        confidence_adjusted = mastery * (0.6 + 0.4 * confidence)

        if confidence_adjusted < 0.25:
            band = "novice"
        elif confidence_adjusted < 0.5:
            band = "developing"
        elif confidence_adjusted < 0.75:
            band = "proficient"
        else:
            band = "expert"

        return {
            "mastery_score": round(mastery, 4),
            "confidence_adjusted_score": round(confidence_adjusted, 4),
            "mastery_band": band,
            "confidence": round(confidence, 4),
        }

    def learning_trends(
        self,
        tenant_id: str,
        learner_id: str,
        skill_id: str,
    ) -> Dict[str, float | str | int]:
        aggregate = self._get_or_create_aggregate(tenant_id, learner_id)
        snapshots = aggregate.trend_snapshots.get(skill_id, [])
        if len(snapshots) < 2:
            return {
                "samples": len(snapshots),
                "trend_slope": 0.0,
                "moving_average": round(snapshots[0][1], 4) if snapshots else 0.0,
                "trend_label": "stable",
            }

        first_at, first_value = snapshots[0]
        last_at, last_value = snapshots[-1]
        span_days = max((last_at - first_at).days, 1)
        slope = (last_value - first_value) / span_days

        trailing_values = [value for _, value in snapshots[-3:]]
        moving_average = fmean(trailing_values)

        if slope > 0.01:
            label = "improving"
        elif slope < -0.01:
            label = "declining"
        else:
            label = "stable"

        return {
            "samples": len(snapshots),
            "trend_slope": round(slope, 4),
            "moving_average": round(moving_average, 4),
            "trend_label": label,
        }

    def get_skill_snapshot(self, tenant_id: str, learner_id: str, skill_id: str) -> Dict[str, object]:
        aggregate = self._get_or_create_aggregate(tenant_id, learner_id)
        skill_state = aggregate.skills.get(skill_id)
        evidence = aggregate.evidence_by_skill.get(skill_id, [])
        return {
            "tenant_id": tenant_id,
            "learner_id": learner_id,
            "skill_id": skill_id,
            "skill_state": asdict(skill_state) if skill_state else None,
            "evidence": [asdict(item) for item in sorted(evidence, key=lambda e: e.evidence_date)],
        }
