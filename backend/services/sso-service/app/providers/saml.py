from __future__ import annotations

from urllib.parse import urlencode
from uuid import uuid4

from app.models import (
    AuthenticatedIdentity,
    CallbackRequest,
    InitiateSSORequest,
    SAMLConfig,
    SSOInitResponse,
)
from app.providers.base import BaseProvider


class SAMLProvider(BaseProvider):
    provider_name = "saml"
    flow_name = "sp_initiated_or_idp_initiated_saml"

    def initiate(self, req: InitiateSSORequest) -> SSOInitResponse:
        cfg = SAMLConfig(**req.config)
        correlation_id = str(uuid4())
        query = urlencode(
            {
                "SAMLRequest": "signed-authn-request-placeholder",
                "RelayState": req.relay_state or "",
                "Tenant": req.tenant_id,
                "CorrelationId": correlation_id,
            }
        )
        return SSOInitResponse(
            provider=req.provider,
            flow=self.flow_name,
            redirect_url=f"{cfg.idp_sso_url}?{query}",
            correlation_id=correlation_id,
        )

    def consume_callback(self, req: CallbackRequest) -> AuthenticatedIdentity:
        payload = req.payload
        self._required(payload, "assertion", "subject")
        return AuthenticatedIdentity(
            tenant_id=req.tenant_id,
            provider=req.provider,
            subject=payload["subject"],
            email=payload.get("email"),
            first_name=payload.get("first_name"),
            last_name=payload.get("last_name"),
            roles=payload.get("roles", []),
            claims=payload,
        )
