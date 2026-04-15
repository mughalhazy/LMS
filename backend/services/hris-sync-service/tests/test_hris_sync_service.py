from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from src.service import HRISSyncService, ValidationError


class HRISSyncServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.service = HRISSyncService()
        self.tenant_id = "tenant-hris"

    def test_role_mapping_sync_upserts_roles(self) -> None:
        created_summary = self.service.sync_roles(
            tenant_id=self.tenant_id,
            role_records=[
                {
                    "role_code": "MGR",
                    "role_name": "Manager",
                    "role_type": "line_management",
                    "permission_bundle": {"course.assign": True},
                    "active_flag": True,
                }
            ],
        )

        updated_summary = self.service.sync_roles(
            tenant_id=self.tenant_id,
            role_records=[
                {
                    "role_code": "MGR",
                    "role_name": "People Manager",
                    "role_type": "line_management",
                    "permission_bundle": {"course.assign": True, "report.view": True},
                    "active_flag": True,
                }
            ],
        )

        self.assertEqual(1, created_summary.created)
        self.assertEqual(1, updated_summary.updated)
        self.assertEqual("People Manager", self.service.list_roles(tenant_id=self.tenant_id)[0].name)

    def test_org_hierarchy_sync_maps_parent_relations(self) -> None:
        summary = self.service.sync_org_hierarchy(
            tenant_id=self.tenant_id,
            department_records=[
                {
                    "department_code": "ENG",
                    "department_name": "Engineering",
                    "parent_department_code": None,
                    "cost_center": "1000",
                    "active_flag": True,
                },
                {
                    "department_code": "PLAT",
                    "department_name": "Platform",
                    "parent_department_code": "ENG",
                    "cost_center": "1100",
                    "active_flag": True,
                },
            ],
        )

        departments = {d.external_hris_code: d for d in self.service.list_departments(tenant_id=self.tenant_id)}

        self.assertEqual(2, summary.created)
        self.assertIsNone(departments["ENG"].parent_department_id)
        self.assertEqual(departments["ENG"].department_id, departments["PLAT"].parent_department_id)

    def test_employee_sync_maps_role_department_and_manager(self) -> None:
        self.service.sync_roles(
            tenant_id=self.tenant_id,
            role_records=[
                {
                    "role_code": "IC",
                    "role_name": "Individual Contributor",
                    "role_type": "worker",
                    "permission_bundle": {"course.enroll": True},
                    "active_flag": True,
                }
            ],
        )
        self.service.sync_org_hierarchy(
            tenant_id=self.tenant_id,
            department_records=[
                {
                    "department_code": "ENG",
                    "department_name": "Engineering",
                    "parent_department_code": None,
                    "cost_center": "1000",
                    "active_flag": True,
                }
            ],
        )

        summary = self.service.sync_employees(
            tenant_id=self.tenant_id,
            employee_records=[
                {
                    "employee_id": "E001",
                    "first_name": "Ava",
                    "last_name": "Manager",
                    "work_email": "ava@example.com",
                    "employment_status": "active",
                    "job_title": "Engineering Manager",
                    "manager_employee_id": None,
                    "department_code": "ENG",
                    "role_code": "IC",
                    "hire_date": "2024-01-15T00:00:00Z",
                    "termination_date": None,
                },
                {
                    "employee_id": "E002",
                    "first_name": "Ben",
                    "last_name": "Engineer",
                    "work_email": "ben@example.com",
                    "employment_status": "active",
                    "job_title": "Software Engineer",
                    "manager_employee_id": "E001",
                    "department_code": "ENG",
                    "role_code": "IC",
                    "hire_date": "2024-03-01",
                    "termination_date": None,
                },
            ],
        )

        users = {u.external_hris_id: u for u in self.service.list_users(tenant_id=self.tenant_id)}

        self.assertEqual(2, summary.created)
        self.assertEqual(users["E001"].user_id, users["E002"].manager_user_id)
        self.assertIsNotNone(users["E002"].department_id)
        self.assertIsNotNone(users["E002"].role_id)

    def test_employee_sync_requires_existing_role_and_department_mapping(self) -> None:
        with self.assertRaises(ValidationError):
            self.service.sync_employees(
                tenant_id=self.tenant_id,
                employee_records=[
                    {
                        "employee_id": "E003",
                        "first_name": "No",
                        "last_name": "Mapping",
                        "work_email": "nomap@example.com",
                        "employment_status": "active",
                        "job_title": "Unknown",
                        "manager_employee_id": None,
                        "department_code": "UNKNOWN",
                        "role_code": "UNKNOWN",
                        "hire_date": None,
                        "termination_date": None,
                    }
                ],
            )

    def test_scheduled_sync_jobs_upsert_and_execute_when_due(self) -> None:
        job = self.service.upsert_sync_job(
            tenant_id=self.tenant_id,
            job_name="nightly_full_sync",
            interval_minutes=60,
            enabled=True,
        )
        self.assertIsNotNone(job.next_run_at)

        due_at = datetime.now(timezone.utc) + timedelta(minutes=61)
        executed = self.service.run_due_sync_jobs(tenant_id=self.tenant_id, as_of=due_at)

        self.assertEqual(1, len(executed))
        self.assertEqual("nightly_full_sync", executed[0].job_name)
        self.assertGreater(executed[0].next_run_at, due_at)


if __name__ == "__main__":
    unittest.main()
