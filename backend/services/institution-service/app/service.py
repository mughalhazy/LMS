from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.audit import AuditEvent, AuditLogger
from app.errors import InstitutionServiceError
from app.events import EventPublisher
from app.models import (
    DomainEvent,
    Institution,
    InstitutionHierarchyEdge,
    InstitutionStatus,
    InstitutionTenantLink,
    InstitutionType,
    LinkScope,
    RelationshipType,
    SYSTEM_INSTITUTION_TYPES,
)
from app.repository import InstitutionRepository


class InstitutionService:
    def __init__(
        self,
        repository: InstitutionRepository,
        audit_logger: AuditLogger | None = None,
        event_publisher: EventPublisher | None = None,
    ) -> None:
        self.repository = repository
        self.audit_logger = audit_logger or AuditLogger()
        self.event_publisher = event_publisher or EventPublisher()
        self._seed_types()

    def _seed_types(self) -> None:
        for code in SYSTEM_INSTITUTION_TYPES:
            if not self.repository.get_type(code):
                self.repository.save_type(
                    InstitutionType(
                        type_code=code,
                        type_name=code.replace("_", " ").title(),
                        is_system_type=True,
                    )
                )

    def create_institution(self, request) -> Institution:
        self._validate_type(request.institution_type)
        institution = Institution(
            institution_id=f"ins_{uuid4().hex[:12]}",
            institution_type=request.institution_type,
            legal_name=request.legal_name,
            display_name=request.display_name,
            tenant_id=request.tenant_id,
            registration_country=request.registration_country,
            default_locale=request.default_locale,
            timezone=request.timezone,
            metadata=request.metadata,
        )
        self.repository.save_institution(institution)
        self._audit("institution.created", request.actor_id, request.tenant_id, institution.institution_id)
        self._publish(
            "institution.created.v1",
            institution.tenant_id,
            institution.institution_id,
            {
                "institution_id": institution.institution_id,
                "institution_type": institution.institution_type,
                "status": institution.status.value,
                "registration_country": institution.registration_country,
                "tenant_id": institution.tenant_id,
            },
        )
        return institution

    def update_institution(self, institution_id: str, request) -> Institution:
        institution = self.get_institution(institution_id)
        self._require_same_tenant(request.actor_id, institution.tenant_id, institution.tenant_id)
        if request.display_name:
            institution.display_name = request.display_name
        if request.default_locale:
            institution.default_locale = request.default_locale
        if request.timezone:
            institution.timezone = request.timezone
        if request.metadata is not None:
            institution.metadata = request.metadata
        institution.updated_at = datetime.now(timezone.utc)
        self.repository.save_institution(institution)
        self._audit("institution.updated", request.actor_id, institution.tenant_id, institution_id)
        return institution

    def transition_status(self, institution_id: str, target_status: InstitutionStatus, actor_id: str, reason: str) -> Institution:
        institution = self.get_institution(institution_id)
        transitions = {
            InstitutionStatus.DRAFT: {InstitutionStatus.ACTIVE, InstitutionStatus.ARCHIVED},
            InstitutionStatus.ACTIVE: {InstitutionStatus.SUSPENDED, InstitutionStatus.ARCHIVED},
            InstitutionStatus.SUSPENDED: {InstitutionStatus.ACTIVE, InstitutionStatus.ARCHIVED},
            InstitutionStatus.ARCHIVED: set(),
        }
        if target_status not in transitions[institution.status]:
            raise InstitutionServiceError("INVALID_STATE_TRANSITION", "Invalid lifecycle transition")
        institution.status = target_status
        institution.updated_at = datetime.now(timezone.utc)
        self.repository.save_institution(institution)
        self._audit(f"institution.{target_status.value}", actor_id, institution.tenant_id, institution_id, {"reason": reason})
        self._publish(
            f"institution.{target_status.value}.v1",
            institution.tenant_id,
            institution_id,
            {"institution_id": institution_id, "reason": reason, "status": target_status.value},
        )
        return institution

    def add_parent_edge(self, child_id: str, request) -> InstitutionHierarchyEdge:
        child = self.get_institution(child_id)
        parent = self.get_institution(request.parent_institution_id)
        self._require_same_tenant(request.actor_id, child.tenant_id, parent.tenant_id)
        relationship_type = RelationshipType(request.relationship_type)

        if child.status == InstitutionStatus.ARCHIVED or parent.status == InstitutionStatus.ARCHIVED:
            raise InstitutionServiceError("INVALID_STATE_TRANSITION", "Archived institutions cannot be linked")

        if relationship_type == RelationshipType.GOVERNANCE_PARENT:
            existing = [e for e in self.repository.list_edges_for_child(child_id) if e.relationship_type == RelationshipType.GOVERNANCE_PARENT]
            if existing:
                raise InstitutionServiceError("HIERARCHY_CONFLICT", "Child already has governance parent")

        if self._creates_cycle(child_id=child_id, candidate_parent_id=parent.institution_id):
            raise InstitutionServiceError("HIERARCHY_CYCLE", "Hierarchy cycle detected")

        edge = InstitutionHierarchyEdge(
            edge_id=f"ied_{uuid4().hex[:12]}",
            parent_institution_id=parent.institution_id,
            child_institution_id=child_id,
            relationship_type=relationship_type,
        )
        self.repository.save_hierarchy_edge(edge)
        self._audit("institution.hierarchy_linked", request.actor_id, child.tenant_id, child_id, {"parent": parent.institution_id})
        self._publish(
            "institution.hierarchy_linked.v1",
            child.tenant_id,
            child_id,
            {
                "parent_institution_id": parent.institution_id,
                "child_institution_id": child_id,
                "relationship_type": relationship_type.value,
            },
        )
        return edge

    def remove_parent_edge(self, child_id: str, parent_id: str, actor_id: str) -> InstitutionHierarchyEdge:
        child = self.get_institution(child_id)
        edge = self.repository.deactivate_edge(child_id, parent_id)
        if not edge:
            raise InstitutionServiceError("NOT_FOUND", "Hierarchy edge not found")
        self._audit("institution.hierarchy_unlinked", actor_id, child.tenant_id, child_id, {"parent": parent_id})
        return edge

    def reparent_institution(self, institution_id: str, request) -> InstitutionHierarchyEdge:
        edges = [e for e in self.repository.list_edges_for_child(institution_id) if e.relationship_type == RelationshipType.GOVERNANCE_PARENT]
        for edge in edges:
            self.repository.deactivate_edge(institution_id, edge.parent_institution_id)
        return self.add_parent_edge(
            institution_id,
            type("EdgeReq", (), {
                "parent_institution_id": request.new_parent_institution_id,
                "relationship_type": request.relationship_type,
                "actor_id": request.actor_id,
                "reason": request.reason,
            })(),
        )

    def create_type(self, request) -> InstitutionType:
        if self.repository.get_type(request.type_code):
            raise InstitutionServiceError("TYPE_EXISTS", "Institution type already exists")
        created = self.repository.save_type(
            InstitutionType(
                type_code=request.type_code,
                type_name=request.type_name,
                governance_profile=request.governance_profile,
            )
        )
        self._publish("institution.type_updated.v1", "system", request.type_code, {"type_code": request.type_code})
        return created

    def list_types(self) -> list[InstitutionType]:
        return self.repository.list_types()

    def create_tenant_link(self, institution_id: str, request) -> InstitutionTenantLink:
        institution = self.get_institution(institution_id)
        self._require_same_tenant(request.actor_id, institution.tenant_id, request.tenant_id)
        if institution.status != InstitutionStatus.ACTIVE and request.link_scope == LinkScope.PRIMARY.value:
            raise InstitutionServiceError("INVALID_STATE_TRANSITION", "Primary link requires active institution")

        links = self.repository.list_links_for_tenant(request.tenant_id)
        if request.link_scope == LinkScope.PRIMARY.value and any(l.link_scope == LinkScope.PRIMARY for l in links):
            raise InstitutionServiceError("TENANT_LINK_CONFLICT", "Tenant already has primary institution link")

        link = InstitutionTenantLink(
            link_id=f"itl_{uuid4().hex[:12]}",
            institution_id=institution_id,
            tenant_id=request.tenant_id,
            link_scope=LinkScope(request.link_scope),
        )
        self.repository.save_tenant_link(link)
        self._audit("institution.tenant_linked", request.actor_id, request.tenant_id, institution_id, {"link_scope": request.link_scope})
        self._publish(
            "institution.tenant_linked.v1",
            request.tenant_id,
            institution_id,
            {
                "institution_id": institution_id,
                "tenant_id": request.tenant_id,
                "link_scope": request.link_scope,
            },
        )
        return link

    def list_tenant_links(self, institution_id: str) -> list[InstitutionTenantLink]:
        self.get_institution(institution_id)
        return self.repository.list_tenant_links(institution_id)

    def resolve_tenant_context(self, tenant_id: str) -> dict:
        links = self.repository.list_links_for_tenant(tenant_id)
        primary = next((l for l in links if l.link_scope == LinkScope.PRIMARY), None)
        return {
            "tenant_id": tenant_id,
            "primary_institution_id": primary.institution_id if primary else None,
            "active_links": [link.link_id for link in links],
        }

    def get_hierarchy(self, institution_id: str) -> dict:
        self.get_institution(institution_id)
        ancestors = []
        current = institution_id
        while True:
            parents = [e for e in self.repository.list_edges_for_child(current) if e.relationship_type == RelationshipType.GOVERNANCE_PARENT]
            if not parents:
                break
            parent = parents[0].parent_institution_id
            ancestors.append(parent)
            current = parent
        descendants = [e.child_institution_id for e in self.repository.list_edges_for_parent(institution_id)]
        root = ancestors[-1] if ancestors else institution_id
        return {"institution_id": institution_id, "ancestors": ancestors, "descendants": descendants, "effective_root_institution_id": root}

    def get_institution(self, institution_id: str) -> Institution:
        institution = self.repository.get_institution(institution_id)
        if not institution:
            raise InstitutionServiceError("NOT_FOUND", "Institution not found")
        return institution

    def _validate_type(self, institution_type: str) -> None:
        if not self.repository.get_type(institution_type):
            raise InstitutionServiceError("TYPE_UNSUPPORTED", f"Institution type {institution_type} is unsupported")

    def _creates_cycle(self, child_id: str, candidate_parent_id: str) -> bool:
        if child_id == candidate_parent_id:
            return True
        stack = [candidate_parent_id]
        visited: set[str] = set()
        while stack:
            node = stack.pop()
            if node == child_id:
                return True
            if node in visited:
                continue
            visited.add(node)
            for edge in self.repository.list_edges_for_child(node):
                if edge.relationship_type == RelationshipType.GOVERNANCE_PARENT:
                    stack.append(edge.parent_institution_id)
        return False

    def _require_same_tenant(self, actor_id: str, institution_tenant: str, actor_tenant: str) -> None:
        if institution_tenant != actor_tenant:
            raise InstitutionServiceError(
                "TENANT_SCOPE_VIOLATION",
                f"actor {actor_id} attempted cross-tenant write: {actor_tenant} -> {institution_tenant}",
            )

    def _audit(self, event_type: str, actor_id: str, tenant_id: str, target_id: str, details: dict | None = None) -> None:
        self.audit_logger.log(
            AuditEvent(
                event_type=event_type,
                actor_id=actor_id,
                tenant_id=tenant_id,
                target_id=target_id,
                details=details or {},
            )
        )

    def _publish(self, event_type: str, tenant_id: str, aggregate_id: str, payload: dict) -> None:
        self.event_publisher.publish(
            DomainEvent(
                event_id=f"evt_{uuid4().hex[:12]}",
                event_type=event_type,
                timestamp=datetime.now(timezone.utc),
                tenant_id=tenant_id,
                correlation_id=str(uuid4()),
                payload=payload,
                metadata={"aggregate_id": aggregate_id, "producer": "institution-service"},
            )
        )
