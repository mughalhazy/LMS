import unittest

from app.errors import InstitutionServiceError
from app.main import InstitutionAPI
from app.schemas import (
    CreateHierarchyEdgeRequest,
    CreateInstitutionRequest,
    CreateTenantLinkRequest,
    TransitionInstitutionRequest,
)


class InstitutionServiceTests(unittest.TestCase):
    def test_lifecycle_hierarchy_and_tenant_context(self) -> None:
        api = InstitutionAPI()

        parent = api.create_institution(
            CreateInstitutionRequest(
                institution_type="academy",
                legal_name="Global Academy Holdings",
                display_name="Global Academy",
                tenant_id="tenant-1",
                registration_country="GB",
                actor_id="admin-1",
            )
        )

        child = api.create_institution(
            CreateInstitutionRequest(
                institution_type="tutor_organization",
                legal_name="Tutor Org Ltd",
                display_name="Tutor Org",
                tenant_id="tenant-1",
                registration_country="GB",
                actor_id="admin-1",
            )
        )

        api.activate_institution(parent.institution_id, TransitionInstitutionRequest(actor_id="admin-1", reason="ready"))
        api.activate_institution(child.institution_id, TransitionInstitutionRequest(actor_id="admin-1", reason="ready"))

        api.add_parent(
            child.institution_id,
            CreateHierarchyEdgeRequest(
                parent_institution_id=parent.institution_id,
                relationship_type="governance_parent",
                actor_id="admin-1",
                reason="initial structure",
            ),
        )

        hierarchy = api.get_hierarchy(child.institution_id)
        self.assertEqual(hierarchy["effective_root_institution_id"], parent.institution_id)

        api.create_tenant_link(
            child.institution_id,
            CreateTenantLinkRequest(
                tenant_id="tenant-1",
                link_scope="primary",
                actor_id="admin-1",
            ),
        )
        context = api.get_tenant_institution_context("tenant-1")
        self.assertEqual(context["primary_institution_id"], child.institution_id)

    def test_prevent_hierarchy_cycles(self) -> None:
        api = InstitutionAPI()
        first = api.create_institution(
            CreateInstitutionRequest(
                institution_type="school",
                legal_name="A",
                display_name="A",
                tenant_id="tenant-2",
                registration_country="US",
                actor_id="admin-2",
            )
        )
        second = api.create_institution(
            CreateInstitutionRequest(
                institution_type="school",
                legal_name="B",
                display_name="B",
                tenant_id="tenant-2",
                registration_country="US",
                actor_id="admin-2",
            )
        )
        api.add_parent(
            second.institution_id,
            CreateHierarchyEdgeRequest(
                parent_institution_id=first.institution_id,
                relationship_type="governance_parent",
                actor_id="admin-2",
                reason="setup",
            ),
        )
        with self.assertRaises(InstitutionServiceError):
            api.add_parent(
                first.institution_id,
                CreateHierarchyEdgeRequest(
                    parent_institution_id=second.institution_id,
                    relationship_type="governance_parent",
                    actor_id="admin-2",
                    reason="should fail",
                ),
            )


if __name__ == "__main__":
    unittest.main()
