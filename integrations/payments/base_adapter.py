from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class PaymentResult:
    ok: bool
    status: str
    payment_id: str | None = None
    provider: str | None = None
    error: str | None = None
    invoice_id: str | None = None


@dataclass(frozen=True)
class PaymentVerificationResult:
    ok: bool
    status: str
    payment_id: str
    provider: str
    error: str | None = None


@dataclass(frozen=True)
class TenantPaymentContext:
    tenant_id: str
    country_code: str


class BasePaymentAdapter(Protocol):
    provider_key: str

    def process_payment(
        self,
        amount: int,
        tenant: TenantPaymentContext,
        invoice_id: str | None = None,
    ) -> PaymentResult:
        """Process a payment for a tenant through the provider."""

    def verify_payment(self, *, payment_id: str, tenant: TenantPaymentContext) -> PaymentVerificationResult:
        """Verify payment state with the provider."""

    def parse_callback(self, payload: dict[str, Any]) -> PaymentVerificationResult | None:
        """Parse async callback payload into a verification signal."""


def normalize_tenant(tenant: Any) -> TenantPaymentContext:
    if isinstance(tenant, TenantPaymentContext):
        return tenant

    if isinstance(tenant, dict):
        tenant_id = str(tenant.get("tenant_id") or tenant.get("id") or "")
        country_code = str(tenant.get("country_code") or "")
        if tenant_id and country_code:
            return TenantPaymentContext(tenant_id=tenant_id, country_code=country_code)

    tenant_id = getattr(tenant, "tenant_id", None) or getattr(tenant, "id", None)
    country_code = getattr(tenant, "country_code", None)
    if tenant_id and country_code:
        return TenantPaymentContext(tenant_id=str(tenant_id), country_code=str(country_code))

    raise ValueError("tenant must include tenant_id and country_code")
