from __future__ import annotations

from uuid import uuid4

from app.models import CallbackRequest, ProviderType, SSOCallbackResponse
from app.providers.base import BaseProvider
from app.providers.oauth2 import OAuth2Provider
from app.providers.oidc import OIDCProvider
from app.providers.saml import SAMLProvider


class SSOService:
    def __init__(self) -> None:
        self.providers: dict[ProviderType, BaseProvider] = {
            ProviderType.SAML: SAMLProvider(),
            ProviderType.OAUTH2: OAuth2Provider(),
            ProviderType.OIDC: OIDCProvider(),
        }

    def provider_matrix(self) -> dict[str, str]:
        return {k.value: v.flow_name for k, v in self.providers.items()}

    def initiate(self, req):
        return self.providers[req.provider].initiate(req)

    def callback(self, req: CallbackRequest) -> SSOCallbackResponse:
        identity = self.providers[req.provider].consume_callback(req)
        return SSOCallbackResponse(
            provider=req.provider,
            flow=self.providers[req.provider].flow_name,
            session_id=f"sso_{uuid4()}",
            identity=identity,
        )
