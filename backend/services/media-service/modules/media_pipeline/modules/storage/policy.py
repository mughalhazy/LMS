"""Access policy enforcement for media retrieval."""

from __future__ import annotations

from dataclasses import dataclass

from .config import PolicyConfig
from .models import AccessTier, AccessToken, MediaAsset


class AccessDeniedError(PermissionError):
    """Raised when a user is not allowed to access the media asset."""


@dataclass(slots=True)
class AccessPolicyEnforcer:
    """Applies tenant and entitlement checks for media access."""

    config: PolicyConfig

    def enforce(self, asset: MediaAsset, token: AccessToken) -> None:
        if token.is_expired():
            raise AccessDeniedError("access token expired")

        if self.config.require_tenant_match and token.tenant_id != asset.tenant_id:
            raise AccessDeniedError("token tenant does not match asset tenant")

        if asset.access_tier == AccessTier.PREMIUM:
            entitlements = token.claims.get("entitlements", [])
            if self.config.premium_entitlement_claim not in entitlements:
                raise AccessDeniedError("premium entitlement required")

        if asset.access_tier == AccessTier.AUTHENTICATED and token.subject == "":
            raise AccessDeniedError("authenticated tier requires user subject")
