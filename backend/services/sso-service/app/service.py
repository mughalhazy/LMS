from __future__ import annotations

import sys
from pathlib import Path
from uuid import uuid4

from app.models import CallbackRequest, ProviderType, SSOCallbackResponse
from app.providers.base import BaseProvider

# MS-ADAPTER-01 (MS§4): core SSOService is provider-unaware.
# Concrete provider imports are banned here — providers are injected
# at construction time via integrations/identity/registry.py.


class SSOService:
    def __init__(self, providers: dict[ProviderType, BaseProvider] | None = None) -> None:
        if providers is None:
            # MS-ADAPTER-01 (MS§4): delegate provider construction to the integration registry
            # so core service code never names a concrete provider class.
            _root = Path(__file__).resolve().parents[4]
            if str(_root) not in sys.path:
                sys.path.insert(0, str(_root))
            from integrations.identity.registry import build_sso_providers  # noqa: PLC0415
            providers = build_sso_providers()
        self.providers: dict[ProviderType, BaseProvider] = providers

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
