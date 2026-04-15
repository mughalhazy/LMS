"""Skill analytics service — proficiency tracking, gap detection, mastery scoring, and trends.

CGAP-081: replaces NotImplementedError stub. Delegates domain operations to src.SkillAnalyticsService
and adds tenant-scoped bulk queries (team/org skill profiles) and skill decay refresh
per skill_analytics_spec.md.

Spec refs: docs/specs/skill_analytics_spec.md
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from entities import RoleSkillRequirement  # noqa: E402
from skill_analytics_service import SkillAnalyticsService  # noqa: E402


class SkillAnalyticsManagementService:
    """Tenant-scoped facade over SkillAnalyticsService per skill_analytics_spec.md.

    Covers all three spec metrics:
    - Skill Progress: baseline, absolute change, velocity, milestone attainment
    - Skill Gap Detection: gap magnitude, severity (critical/moderate/minor), priority ranking
    - Skill Mastery Scoring: composite mastery = assessment + practice + validation + retention,
      confidence-adjusted, mastery bands (novice/developing/proficient/expert)

    Additionally provides:
    - Team/org skill profile aggregation (bulk multi-learner gap view)
    - Skill decay refresh (recompute proficiency after inactivity period)
    """

    def __init__(self) -> None:
        self._svc = SkillAnalyticsService()

    # ------------------------------------------------------------------ #
    # Setup                                                                #
    # ------------------------------------------------------------------ #

    def register_skill(
        self,
        *,
        tenant_id: str,
        skill_id: str,
        name: str,
        difficulty_base: float = 0.0,
    ) -> Any:
        return self._svc.register_skill(tenant_id, skill_id, name, difficulty_base)

    def set_role_requirements(
        self,
        *,
        tenant_id: str,
        role_profile_id: str,
        requirements: list[dict[str, Any]],
    ) -> None:
        """Configure target skill levels for a role profile.

        skill_analytics_spec Skill Gap Detection: target skill requirements by role.
        """
        req_objects = [
            RoleSkillRequirement(
                skill_id=r["skill_id"],
                target_level=float(r["target_level"]),
                business_criticality=float(r.get("business_criticality", 1.0)),
                role_weight=float(r.get("role_weight", 1.0)),
            )
            for r in requirements
        ]
        self._svc.set_role_requirements(tenant_id, role_profile_id, req_objects)

    def set_skill_interventions(
        self,
        *,
        tenant_id: str,
        skill_id: str,
        interventions: list[str],
    ) -> None:
        self._svc.set_interventions(tenant_id, skill_id, interventions)

    # ------------------------------------------------------------------ #
    # Evidence recording                                                   #
    # ------------------------------------------------------------------ #

    def record_evidence(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        skill_id: str,
        evidence_type: str,
        normalized_score: float,
        evidence_date: datetime | None = None,
        verified: bool = False,
        difficulty_weight: float = 1.0,
    ) -> Any:
        """Record a skill evidence event and recompute current proficiency.

        skill_analytics_spec data sources: course completion, practice sessions,
        assessment attempts, peer/manager validation.
        """
        return self._svc.record_evidence(
            tenant_id=tenant_id,
            learner_id=learner_id,
            skill_id=skill_id,
            evidence_type=evidence_type,
            normalized_score=normalized_score,
            evidence_date=evidence_date,
            verified=verified,
            difficulty_weight=difficulty_weight,
        )

    # ------------------------------------------------------------------ #
    # Skill Progress (spec metric 1)                                      #
    # ------------------------------------------------------------------ #

    def get_skill_progress(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        skill_id: str,
        target_level: float,
        time_window_days: int = 30,
    ) -> dict[str, float]:
        """Return progress metrics: baseline, current, absolute_change, velocity, milestone_attainment.

        skill_analytics_spec: absolute change, velocity (change/time_window), milestone attainment %.
        """
        return self._svc.progression_metrics(
            tenant_id, learner_id, skill_id, target_level, time_window_days
        )

    # ------------------------------------------------------------------ #
    # Skill Gap Detection (spec metric 2)                                 #
    # ------------------------------------------------------------------ #

    def detect_skill_gaps(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        role_profile_id: str,
        urgency_factor: float = 1.0,
    ) -> list[dict[str, Any]]:
        """Return ranked gap list with severity and recommended interventions.

        skill_analytics_spec: gap = target_level - current_level, classified as
        critical/moderate/minor/none, prioritized by gap × business_criticality × role_weight × urgency.
        """
        return self._svc.detect_skill_gaps(
            tenant_id, learner_id, role_profile_id, urgency_factor
        )

    # ------------------------------------------------------------------ #
    # Skill Mastery Scoring (spec metric 3)                               #
    # ------------------------------------------------------------------ #

    def get_mastery_score(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        skill_id: str,
        w_assessment: float = 0.35,
        w_practice: float = 0.25,
        w_validation: float = 0.2,
        w_retention: float = 0.2,
    ) -> dict[str, Any]:
        """Return composite mastery score and mastery band.

        skill_analytics_spec: mastery = w_assessment*A + w_practice*P + w_validation*V + w_retention*R
        confidence-adjusted. Bands: novice / developing / proficient / expert.
        """
        return self._svc.mastery_scoring(
            tenant_id, learner_id, skill_id,
            w_assessment=w_assessment,
            w_practice=w_practice,
            w_validation=w_validation,
            w_retention=w_retention,
        )

    def get_learning_trends(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        skill_id: str,
    ) -> dict[str, Any]:
        return self._svc.learning_trends(tenant_id, learner_id, skill_id)

    def get_skill_snapshot(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        skill_id: str,
    ) -> dict[str, Any]:
        return self._svc.get_skill_snapshot(tenant_id, learner_id, skill_id)

    # ------------------------------------------------------------------ #
    # Team / org skill profile (bulk multi-learner)                       #
    # ------------------------------------------------------------------ #

    def get_team_skill_profile(
        self,
        *,
        tenant_id: str,
        learner_ids: list[str],
        role_profile_id: str,
        urgency_factor: float = 1.0,
    ) -> dict[str, Any]:
        """Aggregate gap analysis across a team.

        Returns per-learner gaps plus a team-level summary: average gap per skill,
        learners with critical gaps, skills with widest average gap.
        """
        per_learner: dict[str, list[dict[str, Any]]] = {}
        skill_gap_totals: dict[str, list[float]] = {}
        critical_learners: set[str] = set()

        for learner_id in learner_ids:
            gaps = self.detect_skill_gaps(
                tenant_id=tenant_id,
                learner_id=learner_id,
                role_profile_id=role_profile_id,
                urgency_factor=urgency_factor,
            )
            per_learner[learner_id] = gaps
            for g in gaps:
                skill_gap_totals.setdefault(str(g["skill_id"]), []).append(float(str(g["gap"])))
                if g["severity"] == "critical":
                    critical_learners.add(learner_id)

        avg_gaps = {
            skill_id: round(sum(values) / len(values), 4)
            for skill_id, values in skill_gap_totals.items()
        }
        top_skills = sorted(avg_gaps.items(), key=lambda item: item[1], reverse=True)[:5]

        return {
            "tenant_id": tenant_id,
            "role_profile_id": role_profile_id,
            "team_size": len(learner_ids),
            "per_learner_gaps": per_learner,
            "average_gaps_by_skill": avg_gaps,
            "top_gap_skills": [{"skill_id": s, "avg_gap": g} for s, g in top_skills],
            "learners_with_critical_gaps": sorted(critical_learners),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------ #
    # Skill decay refresh                                                  #
    # ------------------------------------------------------------------ #

    def refresh_decay(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        skill_id: str,
    ) -> dict[str, Any]:
        """Recompute proficiency incorporating decay since last evidence.

        skill_analytics_spec: "Apply confidence adjustment based on evidence volume/quality.
        Recalculate periodically with decay handling to reflect true current mastery."
        Records a synthetic decay-check evidence event to trigger recomputation.
        """
        snapshot_before = self._svc.get_skill_snapshot(tenant_id, learner_id, skill_id)
        current_before = (snapshot_before.get("skill_state") or {}).get("current_level", 0.0)

        # Inject a low-weight recency-neutral observation to trigger decay recompute
        self._svc.record_evidence(
            tenant_id=tenant_id,
            learner_id=learner_id,
            skill_id=skill_id,
            evidence_type="decay_check",
            normalized_score=max(0.0, current_before / 5.0),  # normalise back from 5-scale
            evidence_date=datetime.now(timezone.utc),
            verified=False,
            difficulty_weight=0.1,  # minimal weight so decay doesn't inflate score
        )
        snapshot_after = self._svc.get_skill_snapshot(tenant_id, learner_id, skill_id)
        current_after = (snapshot_after.get("skill_state") or {}).get("current_level", 0.0)
        return {
            "learner_id": learner_id,
            "skill_id": skill_id,
            "level_before": round(float(current_before), 4),
            "level_after": round(float(current_after), 4),
            "delta": round(float(current_after) - float(current_before), 4),
            "refreshed_at": datetime.now(timezone.utc).isoformat(),
        }
