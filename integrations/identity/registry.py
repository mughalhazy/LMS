from __future__ import annotations

import sys
from pathlib import Path

# MS-ADAPTER-01 (MS§4): SSO identity provider registry.
#
# Provider implementations (OIDC, SAML, OAuth2) live in
# backend/services/sso-service/app/providers/.
# This registry is the canonical construction point — core SSOService
# is provider-unaware (accepts injected providers).  Swap any provider
# by passing a custom dict to SSOService.__init__ without touching core code.

_ROOT = Path(__file__).resolve().parents[2]
_SSO_APP_PARENT = _ROOT / "backend" / "services" / "sso-service"
if str(_SSO_APP_PARENT) not in sys.path:
    sys.path.insert(0, str(_SSO_APP_PARENT))

from app.models import ProviderType  # noqa: E402
from app.providers.base import BaseProvider  # noqa: E402
from app.providers.oauth2 import OAuth2Provider  # noqa: E402
from app.providers.oidc import OIDCProvider  # noqa: E402
from app.providers.saml import SAMLProvider  # noqa: E402


def build_sso_providers() -> dict[ProviderType, BaseProvider]:
    """Build the default SSO provider map.

    MS-ADAPTER-01 (MS§4): all identity provider construction lives here.
    Core SSOService receives this dict via __init__ and remains unaware
    of which concrete providers are registered.
    """
    return {
        ProviderType.SAML: SAMLProvider(),
        ProviderType.OAUTH2: OAuth2Provider(),
        ProviderType.OIDC: OIDCProvider(),
    }
