import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unittest

from src.entities import RoleSkillRequirement
from src.skill_analytics_service import SkillAnalyticsService


class SkillAnalyticsServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SkillAnalyticsService()
        self.tenant_id = "tenant-a"
        self.learner_id = "learner-1"
        self.skill_id = "skill-python"

    def test_progression_metrics_computes_change_velocity_and_milestone(self) -> None:
        now = datetime.utcnow()
        self.service.record_evidence(
            tenant_id=self.tenant_id,
            learner_id=self.learner_id,
            skill_id=self.skill_id,
            evidence_type="assessment",
            normalized_score=0.3,
            evidence_date=now - timedelta(days=20),
            verified=True,
        )
        self.service.record_evidence(
            tenant_id=self.tenant_id,
            learner_id=self.learner_id,
            skill_id=self.skill_id,
            evidence_type="assessment",
            normalized_score=0.7,
            evidence_date=now - timedelta(days=2),
            verified=True,
        )

        metrics = self.service.progression_metrics(
            tenant_id=self.tenant_id,
            learner_id=self.learner_id,
            skill_id=self.skill_id,
            target_level=4.0,
            time_window_days=30,
        )

        self.assertEqual(metrics["baseline_proficiency"], 1.5)
        self.assertGreater(metrics["current_proficiency"], metrics["baseline_proficiency"])
        self.assertGreater(metrics["absolute_change"], 0)
        self.assertGreater(metrics["velocity"], 0)
        self.assertGreater(metrics["milestone_attainment"], 0)

    def test_skill_gap_detection_ranks_by_priority(self) -> None:
        self.service.record_evidence(
            tenant_id=self.tenant_id,
            learner_id=self.learner_id,
            skill_id="skill-python",
            evidence_type="assessment",
            normalized_score=0.5,
        )
        self.service.record_evidence(
            tenant_id=self.tenant_id,
            learner_id=self.learner_id,
            skill_id="skill-data-modeling",
            evidence_type="assessment",
            normalized_score=0.2,
        )

        self.service.set_role_requirements(
            tenant_id=self.tenant_id,
            role_profile_id="role-data-eng",
            requirements=[
                RoleSkillRequirement(
                    role_profile_id="role-data-eng",
                    skill_id="skill-python",
                    target_level=4.5,
                    business_criticality=1.1,
                    role_weight=1.0,
                ),
                RoleSkillRequirement(
                    role_profile_id="role-data-eng",
                    skill_id="skill-data-modeling",
                    target_level=4.0,
                    business_criticality=1.3,
                    role_weight=1.2,
                ),
            ],
        )

        gaps = self.service.detect_skill_gaps(
            tenant_id=self.tenant_id,
            learner_id=self.learner_id,
            role_profile_id="role-data-eng",
            urgency_factor=1.2,
        )

        self.assertEqual(len(gaps), 2)
        self.assertGreaterEqual(gaps[0]["priority"], gaps[1]["priority"])
        self.assertIn(gaps[0]["severity"], {"critical", "moderate", "minor", "none"})

    def test_mastery_scoring_produces_confidence_and_band(self) -> None:
        now = datetime.utcnow()
        self.service.record_evidence(
            tenant_id=self.tenant_id,
            learner_id=self.learner_id,
            skill_id=self.skill_id,
            evidence_type="assessment",
            normalized_score=0.8,
            evidence_date=now - timedelta(days=3),
            verified=True,
        )
        self.service.record_evidence(
            tenant_id=self.tenant_id,
            learner_id=self.learner_id,
            skill_id=self.skill_id,
            evidence_type="practice",
            normalized_score=0.75,
            evidence_date=now - timedelta(days=2),
            verified=True,
        )
        self.service.record_evidence(
            tenant_id=self.tenant_id,
            learner_id=self.learner_id,
            skill_id=self.skill_id,
            evidence_type="manager_validation",
            normalized_score=0.9,
            evidence_date=now - timedelta(days=1),
            verified=True,
        )

        mastery = self.service.mastery_scoring(
            tenant_id=self.tenant_id,
            learner_id=self.learner_id,
            skill_id=self.skill_id,
        )

        self.assertGreater(mastery["mastery_score"], 0)
        self.assertGreater(mastery["confidence_adjusted_score"], 0)
        self.assertIn(mastery["mastery_band"], {"novice", "developing", "proficient", "expert"})

    def test_learning_trends_detects_improving_pattern(self) -> None:
        start = datetime.utcnow() - timedelta(days=10)
        for offset, score in enumerate([0.2, 0.4, 0.6, 0.8]):
            self.service.record_evidence(
                tenant_id=self.tenant_id,
                learner_id=self.learner_id,
                skill_id=self.skill_id,
                evidence_type="assessment",
                normalized_score=score,
                evidence_date=start + timedelta(days=offset * 3),
                verified=True,
            )

        trends = self.service.learning_trends(
            tenant_id=self.tenant_id,
            learner_id=self.learner_id,
            skill_id=self.skill_id,
        )

        self.assertEqual(trends["samples"], 4)
        self.assertGreater(trends["trend_slope"], 0)
        self.assertEqual(trends["trend_label"], "improving")


if __name__ == "__main__":
    unittest.main()
