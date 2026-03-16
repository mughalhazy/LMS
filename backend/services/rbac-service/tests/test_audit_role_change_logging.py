from app.models import AssignmentCreate, ScopeType, SubjectType
from app.store import InMemoryRBACStore


def test_role_change_is_audited_with_required_fields() -> None:
    store = InMemoryRBACStore()
    store.create_assignment(
        AssignmentCreate(
            subject_type=SubjectType.USER,
            subject_id="u-1",
            role_id="tenant-admin",
            scope_type=ScopeType.TENANT,
            scope_id="t-1",
            assigned_by="admin-1",
            assignment_model="direct",
        )
    )

    event = store._audit_logger.list_events()[-1]
    assert event.event_type == "rbac.role.assignment.changed"
    assert event.tenant_id == "t-1"
    assert event.actor_id == "admin-1"
    assert event.timestamp is not None
    assert event.destination == "loki"
