from __future__ import annotations

from app.models import (
    Institution,
    InstitutionHierarchyEdge,
    InstitutionTenantLink,
    InstitutionType,
)
from app.store import InMemoryInstitutionStore


class InstitutionRepository:
    """Storage contract implementation that can be replaced by a DB adapter."""

    def __init__(self, store: InMemoryInstitutionStore | None = None) -> None:
        self.store = store or InMemoryInstitutionStore()

    def save_institution(self, institution: Institution) -> Institution:
        self.store.institutions[institution.institution_id] = institution
        return institution

    def get_institution(self, institution_id: str) -> Institution | None:
        return self.store.institutions.get(institution_id)

    def list_tenant_institutions(self, tenant_id: str) -> list[Institution]:
        return [item for item in self.store.institutions.values() if item.tenant_id == tenant_id]

    def save_type(self, institution_type: InstitutionType) -> InstitutionType:
        self.store.institution_types[institution_type.type_code] = institution_type
        return institution_type

    def get_type(self, type_code: str) -> InstitutionType | None:
        return self.store.institution_types.get(type_code)

    def list_types(self) -> list[InstitutionType]:
        return list(self.store.institution_types.values())

    def save_hierarchy_edge(self, edge: InstitutionHierarchyEdge) -> InstitutionHierarchyEdge:
        self.store.hierarchy_edges[edge.edge_id] = edge
        return edge

    def list_edges_for_child(self, child_id: str) -> list[InstitutionHierarchyEdge]:
        return [edge for edge in self.store.hierarchy_edges.values() if edge.child_institution_id == child_id and edge.status == "active"]

    def list_edges_for_parent(self, parent_id: str) -> list[InstitutionHierarchyEdge]:
        return [edge for edge in self.store.hierarchy_edges.values() if edge.parent_institution_id == parent_id and edge.status == "active"]

    def deactivate_edge(self, child_id: str, parent_id: str) -> InstitutionHierarchyEdge | None:
        for edge in self.store.hierarchy_edges.values():
            if edge.child_institution_id == child_id and edge.parent_institution_id == parent_id and edge.status == "active":
                edge.status = "inactive"
                return edge
        return None

    def save_tenant_link(self, link: InstitutionTenantLink) -> InstitutionTenantLink:
        self.store.tenant_links[link.link_id] = link
        return link

    def list_tenant_links(self, institution_id: str) -> list[InstitutionTenantLink]:
        return [link for link in self.store.tenant_links.values() if link.institution_id == institution_id]

    def list_links_for_tenant(self, tenant_id: str) -> list[InstitutionTenantLink]:
        return [link for link in self.store.tenant_links.values() if link.tenant_id == tenant_id and link.status == "active"]

    def deactivate_link(self, link_id: str) -> InstitutionTenantLink | None:
        link = self.store.tenant_links.get(link_id)
        if link:
            link.status = "inactive"
        return link
