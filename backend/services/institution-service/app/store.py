from __future__ import annotations

from app.models import Institution, InstitutionHierarchyEdge, InstitutionTenantLink, InstitutionType


class InMemoryInstitutionStore:
    def __init__(self) -> None:
        self.institutions: dict[str, Institution] = {}
        self.hierarchy_edges: dict[str, InstitutionHierarchyEdge] = {}
        self.tenant_links: dict[str, InstitutionTenantLink] = {}
        self.institution_types: dict[str, InstitutionType] = {}
