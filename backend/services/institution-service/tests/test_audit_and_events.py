from app.main import InstitutionAPI
from app.schemas import CreateInstitutionRequest


def test_mutations_create_audit_and_events() -> None:
    api = InstitutionAPI()
    created = api.create_institution(
        CreateInstitutionRequest(
            institution_type="university",
            legal_name="Example University",
            display_name="EU",
            tenant_id="tenant-3",
            registration_country="DE",
            actor_id="admin-3",
        )
    )

    audit_event = api.service.audit_logger.list_events()[-1]
    emitted_event = api.service.event_publisher.list_events()[-1]

    assert audit_event.event_type == "institution.created"
    assert audit_event.target_id == created.institution_id
    assert emitted_event.event_type == "institution.created.v1"
    assert emitted_event.payload["institution_id"] == created.institution_id
