import unittest

from src.service import DepartmentService, NotFoundError, ValidationError


class DepartmentServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = DepartmentService()
        self.tenant_id = "tenant-1"
        self.organization_id = "org-1"

    def test_department_creation_and_hierarchy(self) -> None:
        root = self.service.create_department(
            tenant_id=self.tenant_id,
            organization_id=self.organization_id,
            name="Engineering",
            code="ENG",
        )
        child = self.service.create_department(
            tenant_id=self.tenant_id,
            organization_id=self.organization_id,
            name="Platform",
            code="PLAT",
            parent_department_id=root.department_id,
        )

        children = self.service.list_children(root.department_id)

        self.assertEqual(1, len(children))
        self.assertEqual(child.department_id, children[0].department_id)

    def test_reparent_validates_cycles(self) -> None:
        parent = self.service.create_department(
            tenant_id=self.tenant_id,
            organization_id=self.organization_id,
            name="Parent",
            code="PARENT",
        )
        child = self.service.create_department(
            tenant_id=self.tenant_id,
            organization_id=self.organization_id,
            name="Child",
            code="CHILD",
            parent_department_id=parent.department_id,
        )

        with self.assertRaises(ValidationError):
            self.service.reparent_department(
                department_id=parent.department_id,
                new_parent_department_id=child.department_id,
            )

    def test_membership_mapping(self) -> None:
        department = self.service.create_department(
            tenant_id=self.tenant_id,
            organization_id=self.organization_id,
            name="Support",
            code="SUP",
        )

        membership = self.service.map_membership(
            tenant_id=self.tenant_id,
            organization_id=self.organization_id,
            department_id=department.department_id,
            user_id="user-123",
            role="member",
        )

        self.assertEqual("user-123", membership.user_id)
        self.assertEqual(1, len(self.service.list_memberships(department.department_id)))

    def test_membership_requires_department(self) -> None:
        with self.assertRaises(NotFoundError):
            self.service.map_membership(
                tenant_id=self.tenant_id,
                organization_id=self.organization_id,
                department_id="missing",
                user_id="user-123",
                role="member",
            )


if __name__ == "__main__":
    unittest.main()
