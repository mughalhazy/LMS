from __future__ import annotations

from urllib.parse import urlencode
from uuid import uuid4

from app.models import (
    AuthenticatedIdentity,
    CallbackRequest,
    InitiateSSORequest,
    OIDCConfig,
    SSOInitResponse,
)
from app.providers.base import BaseProvider


class OIDCProvider(BaseProvider):
    provider_name = "oidc"
    flow_name = "authorization_code_pkce"

    def initiate(self, req: InitiateSSORequest) -> SSOInitResponse:
        cfg = OIDCConfig(**req.config)
        correlation_id = str(uuid4())
        query = urlencode(
            {
                "response_type": "code",
                "client_id": cfg.client_id,
                "redirect_uri": cfg.redirect_uri,
                "scope": " ".join(cfg.scopes),
                "state": req.relay_state or correlation_id,
                "nonce": req.nonce or correlation_id,
                "code_challenge": "pkce-code-challenge-placeholder",
                "code_challenge_method": "S256",
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
        self._required(payload, "code", "id_token", "sub")
        return AuthenticatedIdentity(
            tenant_id=req.tenant_id,
            provider=req.provider,
            subject=payload["sub"],
            email=payload.get("email"),
            first_name=payload.get("given_name"),
            last_name=payload.get("family_name"),
            roles=payload.get("roles", []),
            claims=payload,
        )
