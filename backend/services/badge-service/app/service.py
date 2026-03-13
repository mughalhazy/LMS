from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException

from .models import BadgeDefinition, BadgeIssuance, BadgeIssuanceStatus, BadgeStatus
from .repository import InMemoryBadgeRepository


class BadgeService:
    def __init__(self, repository: InMemoryBadgeRepository) -> None:
        self.repository = repository

    def create_badge_definition(self, payload: dict) -> dict:
        existing = [
            b
            for b in self.repository.list_badges(tenant_id=payload["tenant_id"])
            if b.code.lower() == payload["code"].lower()
        ]
        if existing:
            raise HTTPException(status_code=409, detail="badge code already exists for tenant")

        badge = BadgeDefinition(**payload)
        self.repository.create_badge(badge)
        return self.repository.serialize_badge(badge)

    def patch_badge_definition(self, tenant_id: str, badge_id: str, updates: dict) -> dict:
        badge = self.repository.get_badge(badge_id, tenant_id)
        if not badge:
            raise HTTPException(status_code=404, detail="badge definition not found")

        if "code" in updates:
            raise HTTPException(status_code=400, detail="badge code is immutable")

        for key, value in updates.items():
            setattr(badge, key, value)
        badge.updated_at = datetime.now(timezone.utc)
        return self.repository.serialize_badge(badge)

    def list_badge_definitions(self, tenant_id: str) -> list[dict]:
        return [self.repository.serialize_badge(row) for row in self.repository.list_badges(tenant_id=tenant_id)]

    def issue_badge(self, payload: dict) -> dict:
        badge = self.repository.get_badge(payload["badge_id"], payload["tenant_id"])
        if not badge:
            raise HTTPException(status_code=404, detail="badge definition not found")
        if badge.status != BadgeStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="badge definition is not active")

        existing = self.repository.list_issuances(
            tenant_id=payload["tenant_id"], learner_id=payload["learner_id"], badge_id=payload["badge_id"]
        )
        if any(item.status == BadgeIssuanceStatus.ISSUED for item in existing):
            raise HTTPException(status_code=409, detail="learner already has active issuance for badge")

        issuance = BadgeIssuance(**payload)
        self.repository.create_issuance(issuance)
        return self.repository.serialize_issuance(issuance)

    def patch_badge_issuance(self, tenant_id: str, issuance_id: str, updates: dict) -> dict:
        issuance = self.repository.get_issuance(issuance_id, tenant_id)
        if not issuance:
            raise HTTPException(status_code=404, detail="badge issuance not found")

        if updates.get("status") == BadgeIssuanceStatus.REVOKED and issuance.status != BadgeIssuanceStatus.REVOKED:
            issuance.status = BadgeIssuanceStatus.REVOKED
            issuance.revoked_at = datetime.now(timezone.utc)
            issuance.revoke_reason = updates.get("revoke_reason")
        elif updates.get("status") == BadgeIssuanceStatus.ISSUED:
            issuance.status = BadgeIssuanceStatus.ISSUED
            issuance.revoked_at = None
            issuance.revoke_reason = None

        issuance.updated_at = datetime.now(timezone.utc)
        return self.repository.serialize_issuance(issuance)

    def list_learner_badge_history(self, tenant_id: str, learner_id: str) -> dict:
        issuances = self.repository.list_issuances(tenant_id=tenant_id, learner_id=learner_id)
        out = []
        for issuance in issuances:
            badge = self.repository.get_badge(issuance.badge_id, tenant_id)
            row = self.repository.serialize_issuance(issuance)
            row["badge"] = self.repository.serialize_badge(badge) if badge else None
            out.append(row)
        out.sort(key=lambda x: x["issued_at"], reverse=True)
        return {"tenant_id": tenant_id, "learner_id": learner_id, "badges": out}
