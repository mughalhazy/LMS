from __future__ import annotations

from dataclasses import asdict

from .models import BadgeDefinition, BadgeIssuance


class InMemoryBadgeRepository:
    def __init__(self) -> None:
        self.badges: dict[str, BadgeDefinition] = {}
        self.issuances: dict[str, BadgeIssuance] = {}

    def create_badge(self, badge: BadgeDefinition) -> BadgeDefinition:
        self.badges[badge.badge_id] = badge
        return badge

    def get_badge(self, badge_id: str) -> BadgeDefinition | None:
        return self.badges.get(badge_id)

    def list_badges(self, tenant_id: str | None = None) -> list[BadgeDefinition]:
        rows = self.badges.values()
        if tenant_id:
            rows = [b for b in rows if b.tenant_id == tenant_id]
        return list(rows)

    def create_issuance(self, issuance: BadgeIssuance) -> BadgeIssuance:
        self.issuances[issuance.issuance_id] = issuance
        return issuance

    def get_issuance(self, issuance_id: str) -> BadgeIssuance | None:
        return self.issuances.get(issuance_id)

    def list_issuances(
        self,
        tenant_id: str | None = None,
        learner_id: str | None = None,
        badge_id: str | None = None,
    ) -> list[BadgeIssuance]:
        rows = self.issuances.values()
        if tenant_id:
            rows = [i for i in rows if i.tenant_id == tenant_id]
        if learner_id:
            rows = [i for i in rows if i.learner_id == learner_id]
        if badge_id:
            rows = [i for i in rows if i.badge_id == badge_id]
        return list(rows)

    def serialize_badge(self, badge: BadgeDefinition) -> dict:
        return asdict(badge)

    def serialize_issuance(self, issuance: BadgeIssuance) -> dict:
        return asdict(issuance)
