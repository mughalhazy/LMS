from __future__ import annotations

import base64
import hashlib
import json
import secrets
import time
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


def _generate_pkce_pair() -> tuple[str, str]:
    """Return (code_verifier, code_challenge).  S256 method, stdlib only."""
    code_verifier = secrets.token_urlsafe(32)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    # base64url, no padding
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def _decode_jwt_payload(token: str) -> dict:
    """Decode the payload segment of a JWT without verifying the signature."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return {}
        # base64url may be missing padding
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        return json.loads(base64.urlsafe_b64decode(payload_b64))
    except Exception:
        return {}


class OIDCProvider(BaseProvider):
    provider_name = "oidc"
    flow_name = "authorization_code_pkce"

    def __init__(self) -> None:
        # keyed by correlation_id; holds code_verifier for token exchange validation
        self._pkce_store: dict[str, str] = {}

    def initiate(self, req: InitiateSSORequest) -> SSOInitResponse:
        cfg = OIDCConfig(**req.config)
        correlation_id = str(uuid4())

        code_verifier, code_challenge = _generate_pkce_pair()
        self._pkce_store[correlation_id] = code_verifier

        query = urlencode(
            {
                "response_type": "code",
                "client_id": cfg.client_id,
                "redirect_uri": cfg.redirect_uri,
                "scope": " ".join(cfg.scopes),
                "state": req.relay_state or correlation_id,
                "nonce": req.nonce or correlation_id,
                "code_challenge": code_challenge,
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

        # Basic JWT claim validation on id_token
        id_token = payload.get("id_token", "")
        if id_token:
            claims = _decode_jwt_payload(id_token)
            exp = claims.get("exp")
            if exp is not None and int(exp) < int(time.time()):
                raise ValueError("id_token has expired")

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
