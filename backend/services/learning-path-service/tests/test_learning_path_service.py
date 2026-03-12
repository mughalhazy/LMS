import sys
from pathlib import Path

from datetime import timedelta
import unittest

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.models import CompletionRules, NodeProgress, PathEdge, PathNode, utc_now
from src.service import InMemoryCourseCatalog, LearningPathService, NotFoundError, ValidationError


class LearningPathServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        active_refs = {"course-1", "course-2", "course-3", "assessment-1", "milestone-1"}
        self.service = LearningPathService(course_catalog=InMemoryCourseCatalog(active_refs=active_refs))
        self.tenant_id = "tenant-1"

    def _create_path_with_nodes(self):
        path = self.service.create_learning_path(
            tenant_id=self.tenant_id,
            title="Security Onboarding",
            owner_id="owner-1",
        )
        n1 = PathNode(path_id=path.path_id, node_type="course", ref_id="course-1", sequence_index=1, is_required=True)
        n2 = PathNode(path_id=path.path_id, node_type="course", ref_id="course-2", sequence_index=2, is_required=False)
        n3 = PathNode(path_id=path.path_id, node_type="assessment", ref_id="assessment-1", sequence_index=3, is_required=True)
        self.service.replace_nodes(tenant_id=self.tenant_id, path_id=path.path_id, nodes=[n1, n2, n3], actor_id="owner-1")
        return path, (n1, n2, n3)

    def test_learning_path_creation_is_tenant_scoped(self) -> None:
        path = self.service.create_learning_path(
            tenant_id=self.tenant_id,
            title="Data Privacy",
            owner_id="owner-1",
        )

        with self.assertRaises(NotFoundError):
            self.service.publish_learning_path(
                tenant_id="tenant-2",
                path_id=path.path_id,
                actor_id="owner-2",
                change_reason="wrong tenant",
            )

    def test_course_sequence_validates_cycles(self) -> None:
        path, (n1, n2, n3) = self._create_path_with_nodes()

        cycle_edges = [
            PathEdge(path_id=path.path_id, from_node_id=n1.node_id, to_node_id=n2.node_id, relation="next"),
            PathEdge(path_id=path.path_id, from_node_id=n2.node_id, to_node_id=n3.node_id, relation="next"),
            PathEdge(path_id=path.path_id, from_node_id=n3.node_id, to_node_id=n1.node_id, relation="next"),
        ]

        with self.assertRaises(ValidationError):
            self.service.replace_edges(
                tenant_id=self.tenant_id,
                path_id=path.path_id,
                edges=cycle_edges,
                actor_id="owner-1",
            )

    def test_publish_validates_active_references(self) -> None:
        path = self.service.create_learning_path(
            tenant_id=self.tenant_id,
            title="Compliance",
            owner_id="owner-1",
        )
        node = PathNode(path_id=path.path_id, node_type="course", ref_id="inactive-course", sequence_index=1, is_required=True)
        self.service.replace_nodes(tenant_id=self.tenant_id, path_id=path.path_id, nodes=[node], actor_id="owner-1")

        with self.assertRaises(ValidationError):
            self.service.publish_learning_path(
                tenant_id=self.tenant_id,
                path_id=path.path_id,
                actor_id="owner-1",
                change_reason="publish",
            )

    def test_completion_rules_required_plus_electives(self) -> None:
        path, (n1, n2, n3) = self._create_path_with_nodes()
        self.service.replace_edges(
            tenant_id=self.tenant_id,
            path_id=path.path_id,
            edges=[PathEdge(path_id=path.path_id, from_node_id=n1.node_id, to_node_id=n3.node_id, relation="next")],
            actor_id="owner-1",
        )
        self.service.configure_completion_rules(
            tenant_id=self.tenant_id,
            path_id=path.path_id,
            rules=CompletionRules(mode="required_plus_n_electives", required_plus_n_electives=1),
            actor_id="owner-1",
            change_reason="require elective",
        )

        progress = {
            n1.node_id: NodeProgress(completed=True),
            n3.node_id: NodeProgress(completed=True),
        }
        self.assertIsNone(
            self.service.evaluate_completion(tenant_id=self.tenant_id, path_id=path.path_id, progress_by_node_id=progress).completed_at
        )

        progress[n2.node_id] = NodeProgress(completed=True)
        self.assertIsNotNone(
            self.service.evaluate_completion(tenant_id=self.tenant_id, path_id=path.path_id, progress_by_node_id=progress).completed_at
        )

    def test_due_date_strict_mode_blocks_completion(self) -> None:
        path = self.service.create_learning_path(
            tenant_id=self.tenant_id,
            title="Annual Safety",
            owner_id="owner-1",
            completion_rules=CompletionRules(mode="all_required_complete", strict_due_date=True, due_date=utc_now() - timedelta(days=1)),
        )
        node = PathNode(path_id=path.path_id, node_type="course", ref_id="course-1", sequence_index=1, is_required=True)
        self.service.replace_nodes(tenant_id=self.tenant_id, path_id=path.path_id, nodes=[node], actor_id="owner-1")

        result = self.service.evaluate_completion(
            tenant_id=self.tenant_id,
            path_id=path.path_id,
            progress_by_node_id={node.node_id: NodeProgress(completed=True)},
        )
        self.assertTrue(result.overdue)
        self.assertIsNone(result.completed_at)


if __name__ == "__main__":
    unittest.main()
