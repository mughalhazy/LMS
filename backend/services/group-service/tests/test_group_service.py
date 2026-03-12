from src.group_service import GroupService, ValidationError
from src.models import AssignmentTarget, AssignmentType, GroupStatus


def test_group_lifecycle_membership_and_assignment_flow():
    service = GroupService()

    group = service.create_group(
        tenant_id="tenant-1",
        organization_id="org-1",
        name="Platform Engineering",
        code="PLAT-ENG",
        created_by="admin-1",
    )
    assert group.status == GroupStatus.DRAFT

    service.transition_group_status(group.group_id, GroupStatus.ACTIVE)
    member = service.add_member(
        tenant_id="tenant-1",
        group_id=group.group_id,
        user_id="user-1",
        role="learner",
        added_by="admin-1",
    )
    assert member.user_id == "user-1"

    assignment = service.assign_learning(
        tenant_id="tenant-1",
        group_id=group.group_id,
        assignment_type=AssignmentType.COURSE,
        learning_object_id="course-1",
        target=AssignmentTarget.CURRENT_AND_FUTURE_MEMBERS,
        assigned_by="admin-1",
    )
    assert assignment.learning_object_id == "course-1"


def test_cannot_archive_with_active_members():
    service = GroupService()
    group = service.create_group(
        tenant_id="tenant-1",
        organization_id="org-1",
        name="Security",
        code="SEC",
        created_by="admin-1",
    )
    service.transition_group_status(group.group_id, GroupStatus.ACTIVE)
    service.add_member(
        tenant_id="tenant-1",
        group_id=group.group_id,
        user_id="user-2",
        role="learner",
        added_by="admin-1",
    )

    try:
        service.transition_group_status(group.group_id, GroupStatus.ARCHIVED)
    except ValidationError as error:
        assert "active memberships" in str(error)
    else:
        raise AssertionError("Expected ValidationError")
