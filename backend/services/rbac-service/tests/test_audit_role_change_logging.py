import os

from app.events import InMemoryEventPublisher, InMemoryObservabilityHook
from app.schemas import AssignmentCreateRequest, RoleCreateRequest
from app.service import RBACService
from app.store import InMemoryRBACStore

os.environ["JWT_SHARED_SECRET"] = "test-secret"


def test_assignment_change_publishes_event_and_metrics() -> None:
    store = InMemoryRBACStore()
    publisher = InMemoryEventPublisher()
    obs = InMemoryObservabilityHook()
    service = RBACService(store, publisher, obs)

    role = service.create_role("t-1", RoleCreateRequest(role_key="tenant-admin", display_name="Tenant Admin", description="admin"))
    service.replace_role_permissions("t-1", role.role_id, ["audit.view_tenant"])
    service.create_assignment(
        "t-1",
        AssignmentCreateRequest(
            subject_type="user",
            subject_id="u-1",
            role_id=role.role_id,
            scope_type="tenant",
            scope_id="t-1",
            created_by="admin-1",
        ),
    )

    assert any(e["event_type"] == "rbac.assignment.created.v1" for e in publisher.published)
    assert obs.counters["rbac_role_create_total|tenant_id:t-1"] == 1
