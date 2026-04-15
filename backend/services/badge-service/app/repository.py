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

    def get_badge(self, badge_id: str, tenant_id: str) -> BadgeDefinition | None:
        badge = self.badges.get(badge_id)
        if not badge or badge.tenant_id != tenant_id:
            return None
        return badge

    def list_badges(self, tenant_id: str) -> list[BadgeDefinition]:
        rows = self.badges.values()
        return [b for b in rows if b.tenant_id == tenant_id]

    def create_issuance(self, issuance: BadgeIssuance) -> BadgeIssuance:
        self.issuances[issuance.issuance_id] = issuance
        return issuance

    def get_issuance(self, issuance_id: str, tenant_id: str) -> BadgeIssuance | None:
        issuance = self.issuances.get(issuance_id)
        if not issuance or issuance.tenant_id != tenant_id:
            return None
        return issuance

    def list_issuances(
        self,
        tenant_id: str,
        learner_id: str | None = None,
        badge_id: str | None = None,
    ) -> list[BadgeIssuance]:
        rows = self.issuances.values()
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
