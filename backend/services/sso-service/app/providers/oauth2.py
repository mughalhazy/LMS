from __future__ import annotations

from urllib.parse import urlencode
from uuid import uuid4

from app.models import (
    AuthenticatedIdentity,
    CallbackRequest,
    InitiateSSORequest,
    OAuth2Config,
    SSOInitResponse,
)
from app.providers.base import BaseProvider


class OAuth2Provider(BaseProvider):
    provider_name = "oauth2"
    flow_name = "authorization_code"

    def initiate(self, req: InitiateSSORequest) -> SSOInitResponse:
        cfg = OAuth2Config(**req.config)
        correlation_id = str(uuid4())
        query = urlencode(
            {
                "response_type": "code",
                "client_id": cfg.client_id,
                "redirect_uri": cfg.redirect_uri,
                "scope": " ".join(cfg.scopes),
                "state": req.relay_state or correlation_id,
            }
        )
        return SSOInitResponse(
            provider=req.provider,
            flow=self.flow_name,
            redirect_url=f"{cfg.authorization_endpoint}?{query}",
            correlation_id=correlation_id,
        )

    def consume_callback(self, req: CallbackRequest) -> AuthenticatedIdentity:
        payload = req.payload
        self._required(payload, "code", "subject")
        return AuthenticatedIdentity(
            tenant_id=req.tenant_id,
            provider=req.provider,
            subject=payload["subject"],
            email=payload.get("email"),
            roles=payload.get("roles", []),
            claims=payload,
        )
