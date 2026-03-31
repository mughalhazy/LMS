from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


class MediaAccessError(ValueError):
    """Raised when media access validation fails."""


@dataclass(frozen=True)
class AccessClaims:
    tenant_id: str
    asset_id: str
    profile: str
    access_tier: str
    expires_at: datetime
    watermark_text: str | None = None


class MediaSecurity:
    """Token-based URL security and watermark claim encoder for media assets."""

    def __init__(self, signing_secret: str = "media-service-local-secret") -> None:
        self._signing_secret = signing_secret.encode("utf-8")

    def token_for(self, claims: AccessClaims) -> str:
        expires = str(int(claims.expires_at.timestamp()))
        raw_claim = "|".join(
            [
                claims.tenant_id,
                claims.asset_id,
                claims.profile,
                claims.access_tier,
                expires,
                claims.watermark_text or "",
            ]
        )
        digest = hmac.new(self._signing_secret, raw_claim.encode("utf-8"), hashlib.sha256).hexdigest()
        return digest

    def secure_url(self, base_url: str, claims: AccessClaims) -> str:
        token = self.token_for(claims)
        parsed = urlparse(base_url)
        query = parse_qs(parsed.query)
        query["token"] = [token]
        query["exp"] = [str(int(claims.expires_at.timestamp()))]
        query["tid"] = [claims.tenant_id]
        query["aid"] = [claims.asset_id]
        query["profile"] = [claims.profile]
        if claims.watermark_text:
            query["wm"] = [claims.watermark_text]

        encoded_query = urlencode(query, doseq=True)
        return urlunparse(parsed._replace(query=encoded_query))

    def validate_url(
        self,
        secure_url: str,
        *,
        tenant_id: str,
        asset_id: str,
        profile: str,
        access_tier: str,
        now: datetime | None = None,
    ) -> bool:
        parsed = urlparse(secure_url)
        query = parse_qs(parsed.query)
        token = self._get_first(query, "token")
        expires = self._get_first(query, "exp")
        request_tenant_id = self._get_first(query, "tid")
        request_asset_id = self._get_first(query, "aid")
        request_profile = self._get_first(query, "profile")
        watermark_text = self._get_first(query, "wm", required=False)

        if request_tenant_id != tenant_id or request_asset_id != asset_id or request_profile != profile:
            return False

        expires_at = datetime.fromtimestamp(int(expires), tz=timezone.utc)
        observed_time = now or datetime.now(timezone.utc)
        if observed_time >= expires_at:
            return False

        claims = AccessClaims(
            tenant_id=tenant_id,
            asset_id=asset_id,
            profile=profile,
            access_tier=access_tier,
            expires_at=expires_at,
            watermark_text=watermark_text,
        )
        expected_token = self.token_for(claims)
        return hmac.compare_digest(token, expected_token)

    @staticmethod
    def expiry_from_ttl(ttl_seconds: int) -> datetime:
        ttl = max(1, ttl_seconds)
        return datetime.now(timezone.utc) + timedelta(seconds=ttl)

    def _get_first(self, query: dict[str, list[str]], key: str, *, required: bool = True) -> str:
        values = query.get(key)
        if values and values[0]:
            return values[0]
        if required:
            raise MediaAccessError(f"missing required URL query parameter '{key}'")
        return ""
