from __future__ import annotations

import base64
import zlib
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
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


def _build_authn_request(
    *,
    idp_sso_url: str,
    sp_entity_id: str,
    acs_url: str,
    correlation_id: str,
) -> str:
    """Build a minimal SAML 2.0 AuthnRequest, deflate-compress it, and return Base64."""
    issue_instant = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    root = ET.Element(
        "samlp:AuthnRequest",
        attrib={
            "xmlns:samlp": "urn:oasis:names:tc:SAML:2.0:protocol",
            "xmlns:saml": "urn:oasis:names:tc:SAML:2.0:assertion",
            "ID": f"_{correlation_id.replace('-', '')}",
            "Version": "2.0",
            "IssueInstant": issue_instant,
            "Destination": idp_sso_url,
            "AssertionConsumerServiceURL": acs_url,
            "ProtocolBinding": "urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST",
        },
    )
    issuer = ET.SubElement(root, "saml:Issuer")
    issuer.text = sp_entity_id

    ET.SubElement(
        root,
        "samlp:NameIDPolicy",
        attrib={
            "Format": "urn:oasis:names:tc:SAML:1.1:nameid-format:emailAddress",
            "AllowCreate": "true",
        },
    )

    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)

    # Raw DEFLATE (wbits=-15) as required by SAML HTTP-Redirect binding
    compressor = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION, zlib.DEFLATED, -15)
    deflated = compressor.compress(xml_bytes) + compressor.flush()
    return base64.b64encode(deflated).decode("ascii")


class SAMLProvider(BaseProvider):
    provider_name = "saml"
    flow_name = "sp_initiated_or_idp_initiated_saml"

    def initiate(self, req: InitiateSSORequest) -> SSOInitResponse:
        cfg = SAMLConfig(**req.config)
        correlation_id = str(uuid4())

        saml_request = _build_authn_request(
            idp_sso_url=cfg.idp_sso_url,
            sp_entity_id=getattr(cfg, "sp_entity_id", req.tenant_id),
            acs_url=getattr(cfg, "acs_url", ""),
            correlation_id=correlation_id,
        )

        query = urlencode(
            {
                "SAMLRequest": saml_request,
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
