import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import unittest

from src.entities import CourseSkillMapping, LearnerSkillEvidence, SkillEdge, SkillNode
from src.skill_inference_service import SkillInferenceService


class SkillInferenceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = SkillInferenceService()
        self.service.upsert_skill(SkillNode(skill_id="s-python", name="Python", category_id="cat-dev"))
        self.service.upsert_skill(SkillNode(skill_id="s-data", name="Data Analysis", category_id="cat-dev"))
        self.service.upsert_skill(SkillNode(skill_id="s-ml", name="Machine Learning", category_id="cat-ai"))
        self.service.add_skill_relation(
            SkillEdge(
                source_skill_id="s-python",
                target_skill_id="s-ml",
                relation_type="PREREQUISITE_OF",
            )
        )
        self.service.add_skill_relation(
            SkillEdge(
                source_skill_id="s-data",
                target_skill_id="s-ml",
                relation_type="RELATED_TO",
                relation_weight=0.7,
            )
        )

    def test_infer_learner_skills_updates_levels_and_predictions(self) -> None:
        now = datetime.utcnow()
        self.service.ingest_evidence(
            LearnerSkillEvidence(
                tenant_id="tenant-a",
                learner_id="learner-1",
                skill_id="s-python",
                evidence_id="ev-1",
                evidence_type="assessment",
                normalized_score=0.92,
                confidence_weight=1.0,
                occurred_at=now - timedelta(days=2),
                verified=True,
            )
        )
        self.service.ingest_evidence(
            LearnerSkillEvidence(
                tenant_id="tenant-a",
                learner_id="learner-1",
                skill_id="s-ml",
                evidence_id="ev-2",
                evidence_type="quiz",
                normalized_score=0.85,
                confidence_weight=0.9,
                occurred_at=now - timedelta(days=3),
                verified=False,
            )
        )

        result = self.service.infer_learner_skills("tenant-a", "learner-1", as_of=now)

        self.assertIn("s-python", result.updated_skills)
        self.assertIn("s-ml", result.updated_skills)
        self.assertGreaterEqual(result.updated_skills["s-python"].current_level, 4)
        self.assertIn(
            result.updated_skills["s-python"].predicted_mastery_band,
            {"proficient", "expert"},
        )

    def test_prerequisite_and_related_edges_adjust_skill_state(self) -> None:
        now = datetime.utcnow()
        self.service.ingest_evidence(
            LearnerSkillEvidence(
                tenant_id="tenant-a",
                learner_id="learner-2",
                skill_id="s-python",
                evidence_id="ev-3",
                evidence_type="assessment",
                normalized_score=0.2,
                confidence_weight=1.0,
                occurred_at=now,
            )
        )
        self.service.ingest_evidence(
            LearnerSkillEvidence(
                tenant_id="tenant-a",
                learner_id="learner-2",
                skill_id="s-data",
                evidence_id="ev-4",
                evidence_type="project",
                normalized_score=0.9,
                confidence_weight=1.0,
                occurred_at=now,
            )
        )
        self.service.ingest_evidence(
            LearnerSkillEvidence(
                tenant_id="tenant-a",
                learner_id="learner-2",
                skill_id="s-ml",
                evidence_id="ev-5",
                evidence_type="assessment",
                normalized_score=1.0,
                confidence_weight=1.0,
                occurred_at=now,
            )
        )

        profile = self.service.infer_learner_skills("tenant-a", "learner-2", as_of=now).updated_skills

        self.assertLessEqual(profile["s-ml"].current_level, profile["s-python"].current_level + 1)
        self.assertGreater(profile["s-ml"].mastery_score, 0.0)

    def test_course_completion_infers_mapped_skills(self) -> None:
        self.service.map_course_to_skill(
            CourseSkillMapping(
                course_id="course-ai-101",
                skill_id="s-ml",
                coverage_level="intermediate",
                skill_gain_expected=0.8,
                evidence_weight=0.9,
            )
        )

        result = self.service.infer_skills_from_course_completion(
            tenant_id="tenant-a",
            learner_id="learner-3",
            course_id="course-ai-101",
            completion_score=0.95,
        )

        self.assertIn("s-ml", result.updated_skills)
        self.assertGreater(result.updated_skills["s-ml"].mastery_score, 0.7)

    def test_tenant_isolation(self) -> None:
        now = datetime.utcnow()
        self.service.ingest_evidence(
            LearnerSkillEvidence(
                tenant_id="tenant-a",
                learner_id="learner-1",
                skill_id="s-python",
                evidence_id="ev-6",
                evidence_type="assessment",
                normalized_score=0.8,
                confidence_weight=0.8,
                occurred_at=now,
            )
        )
        self.service.infer_learner_skills("tenant-a", "learner-1", as_of=now)

        profile_other_tenant = self.service.get_learner_skill_profile("tenant-b", "learner-1")
        self.assertEqual(profile_other_tenant, {})


if __name__ == "__main__":
    unittest.main()
