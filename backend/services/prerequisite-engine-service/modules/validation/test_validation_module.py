from datetime import datetime, timedelta
import os
import sys
import unittest

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from validation import (  # noqa: E402
    CourseCatalogEntry,
    CoursePrerequisiteRule,
    CoursePrerequisiteValidator,
    DependencyType,
    EquivalencyMapping,
    LearnerEligibilityValidator,
    LearnerProfile,
    LearningPathEdge,
    LearningPathNode,
    LearningPathProgressionValidator,
    NodeProgress,
    PrerequisiteNode,
    TranscriptRecord,
)


class ValidationModuleTests(unittest.TestCase):
    def test_learner_eligibility(self):
        learner = LearnerProfile(
            learner_id="learner_1",
            tenant_id="tenant_a",
            is_active=True,
            roles=("learner",),
            departments=("engineering",),
        )
        course = CourseCatalogEntry(
            course_id="course_1",
            tenant_id="tenant_a",
            status="published",
            audience_roles=("learner", "manager"),
        )
        result = LearnerEligibilityValidator.validate(learner, course)
        self.assertTrue(result.eligible)

    def test_course_prerequisite_equivalency_and_grade(self):
        rule = CoursePrerequisiteRule(
            target_course_id="course_advanced",
            prerequisite_nodes=(
                PrerequisiteNode(
                    node_id="node_foundation",
                    required_course_ids=("course_foundation",),
                    operator="AND",
                    minimum_grade=80,
                ),
            ),
        )
        transcript = [
            TranscriptRecord(
                course_id="course_foundation_equivalent",
                completion_status="completed",
                score=85,
                completed_at=datetime.utcnow() - timedelta(days=30),
            )
        ]
        equivalencies = [
            EquivalencyMapping(
                source_course_id="course_foundation",
                equivalent_course_ids=("course_foundation_equivalent",),
            )
        ]
        result = CoursePrerequisiteValidator.validate_enrollment_prerequisites(
            rule=rule,
            transcript=transcript,
            equivalencies=equivalencies,
        )
        self.assertEqual(result.enrollment_decision.value, "approved")

    def test_learning_path_progression_strict_and_advisory(self):
        nodes = [
            LearningPathNode(node_id="A", strict_dependency=DependencyType.STRICT, minimum_score=70),
            LearningPathNode(node_id="B", strict_dependency=DependencyType.STRICT),
            LearningPathNode(node_id="C", strict_dependency=DependencyType.ADVISORY),
        ]
        edges = [
            LearningPathEdge(from_node_id="A", to_node_id="B", dependency_type=DependencyType.STRICT),
            LearningPathEdge(from_node_id="B", to_node_id="C", dependency_type=DependencyType.ADVISORY),
        ]
        progress = [
            NodeProgress(node_id="A", completion_status="completed", score=75),
        ]
        result = LearningPathProgressionValidator.validate_progression_requirements(
            nodes=nodes,
            edges=edges,
            progress=progress,
        )
        self.assertIn("B", result.unlocked_nodes)
        self.assertIn("C", result.unlocked_nodes)
        self.assertTrue(any(w.startswith("advisory_dependency_unmet") for w in result.advisory_warnings))


if __name__ == "__main__":
    unittest.main()
