from __future__ import annotations

import asyncio
import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

from .billing import BillingService, InvoiceRecord
from .catalog import CatalogService
from .models import Product, ProductType
from .checkout import CheckoutService, Order, OrderStatus
from .monetization import CapabilityCharge, CapabilityMonetizationService

sys.path.append(str(Path(__file__).resolve().parents[2]))
from integrations.payments.base_adapter import TenantPaymentContext
from integrations.payments.orchestration import PaymentOrchestrationService
from shared.utils.entitlement import TenantEntitlementContext

_ROOT = Path(__file__).resolve().parents[2]


def _load_module(module_name: str, relative_path: str):
    module_path = _ROOT / relative_path
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module from {relative_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


_SubscriptionModule = _load_module("subscription_service_module_for_commerce", "services/subscription-service/service.py")
_ConfigModule = _load_module("config_service_module_for_commerce", "services/config-service/service.py")
_EntitlementModule = _load_module("entitlement_service_module_for_commerce", "services/entitlement-service/service.py")

SubscriptionService = _SubscriptionModule.SubscriptionService
ConfigService = _ConfigModule.ConfigService
ConfigResolutionContext = _ConfigModule.ConfigResolutionContext
EntitlementService = _EntitlementModule.EntitlementService


class CommerceService:
    """Commerce completion layer orchestrating catalog, checkout, and billing modules."""

    def __init__(self, *, payment_orchestrator: PaymentOrchestrationService) -> None:
        self.catalog = CatalogService()
        self.billing = BillingService()
        self.subscription_service = SubscriptionService()
        self.config_service = ConfigService()
        self.entitlement_service = EntitlementService(
            subscription_service=self.subscription_service,
            config_service=self.config_service,
        )
        self.checkout = CheckoutService(self.catalog, self._execute_payment, self._resolve_product_amount)
        self.monetization = CapabilityMonetizationService(
            subscription_service=self.subscription_service,
            capability_registry=self.entitlement_service._capability_registry,
            entitlement_service=self.entitlement_service,
        )
        self._payment_orchestrator = payment_orchestrator

    def add_product(
        self,
        *,
        product_id: str,
        tenant_id: str,
        type: ProductType,
        title: str,
        description: str,
        price: Decimal,
        currency: str,
        capability_ids: list[str],
        metadata: dict[str, str] | None = None,
    ) -> Product:
        product = self.catalog.create_product(
            product_id=product_id,
            tenant_id=tenant_id,
            type=type,
            title=title,
            description=description,
            price=price,
            currency=currency,
            capability_ids=capability_ids,
            metadata=metadata or {},
        )
        return product

    def _resolve_product_amount(self, product: Product) -> Decimal:
        return self.monetization.quote_product_amount(product)

    def _execute_payment(
        self,
        tenant_id: str,
        learner_id: str,
        amount: Decimal,
        currency: str,
        attempt: int,
    ) -> tuple[bool, str | None, bool]:
        ctx = TenantEntitlementContext(
            tenant_id=tenant_id,
            country_code="US",
            segment_id="academy",
            plan_type="pro",
            add_ons=(),
        )
        config = self.config_service.resolve(
            ConfigResolutionContext(tenant_id=tenant_id, country_code="US", segment_id="academy")
        )
        max_attempts = int(config.behavior_tuning.get("commerce.checkout.max_payment_retries", 2)) + 1
        if attempt >= max_attempts:
            return False, None, False

        payment_tenant = TenantPaymentContext(tenant_id=tenant_id, country_code=ctx.country_code)
        entry = self._payment_orchestrator.process_checkout_payment(
            idempotency_key=f"{tenant_id}:{learner_id}:{attempt}",
            tenant=payment_tenant,
            amount=int(amount * 100),
            currency=currency,
            invoice_id=None,
        )
        if entry.status in {"pending_verification", "verified"} and entry.payment_id:
            return True, entry.payment_id, False
        return False, None, bool(entry.error and "timeout" in entry.error.lower())

    async def checkout_and_invoice(
        self,
        *,
        session_id: str,
        tenant_id: str,
        learner_id: str,
        product_id: str,
        idempotency_key: str,
    ) -> tuple[Order, InvoiceRecord]:
        self.checkout.start_session(
            session_id=session_id,
            tenant_id=tenant_id,
            learner_id=learner_id,
            product_id=product_id,
            idempotency_key=idempotency_key,
        )
        order = await self.checkout.submit_session(session_id=session_id)
        if order.status not in {OrderStatus.PAID, OrderStatus.RECONCILED}:
            raise ValueError(f"cannot invoice unpaid order '{order.order_id}'")
        invoice = self.billing.create_invoice_for_order(order)
        order = self.checkout.reconcile_order(order_id=order.order_id)
        if invoice.invoice_type == "subscription":
            self.subscription_service.create_or_activate_subscription(
                tenant_id=tenant_id,
                subscription_id=f"sub_{tenant_id}_{product_id}",
                plan_type="pro",
                source_order_id=order.order_id,
            )
        return order, invoice

    def checkout_and_invoice_sync(self, **kwargs: str):
        return asyncio.run(self.checkout_and_invoice(**kwargs))


    def enable_capability_add_on(self, *, tenant_id: str, capability_id: str) -> None:
        self.monetization.enable_add_on(tenant_id=tenant_id, capability_id=capability_id)

    def record_capability_usage(self, *, tenant_id: str, capability_id: str, units: int = 1) -> None:
        self.monetization.usage_billing_hook(tenant_id=tenant_id, capability_id=capability_id, units=units)

    def calculate_capability_charges(self, tenant: TenantEntitlementContext) -> list[CapabilityCharge]:
        return self.monetization.calculate_tenant_capability_charges(tenant)


def build_commerce_service_for_pakistan(default_provider: str = "jazzcash") -> CommerceService:
    from integrations.payments.orchestration import build_pakistan_payment_orchestration

    return CommerceService(
        payment_orchestrator=build_pakistan_payment_orchestration(default_provider=default_provider)
    )
