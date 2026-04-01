from __future__ import annotations

import asyncio
import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

from .billing import BillingService, InvoiceRecord, InvoiceStatus
from .catalog import CatalogService
from .checkout import CheckoutService, Order, OrderStatus, Transaction, TransactionStatus
from .models import Bundle, Product, ProductType
from .monetization import CapabilityCharge, CapabilityMonetizationService

sys.path.append(str(Path(__file__).resolve().parents[2]))
from integrations.payments.base_adapter import TenantPaymentContext
from integrations.payments.reconciliation import PaymentReconciliationEngine
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
    def __init__(self, *, payment_orchestrator: PaymentOrchestrationService, payment_country_code: str = "US") -> None:
        self.catalog = CatalogService()
        self.billing = BillingService()
        self.subscription_service = SubscriptionService()
        self.config_service = ConfigService()
        self.entitlement_service = EntitlementService(subscription_service=self.subscription_service, config_service=self.config_service)
        self.checkout = CheckoutService(self.catalog, self._execute_payment, self._resolve_product_amount)
        self.monetization = CapabilityMonetizationService(
            subscription_service=self.subscription_service,
            capability_registry=self.entitlement_service._capability_registry,
            entitlement_service=self.entitlement_service,
        )
        self._payment_orchestrator = payment_orchestrator
        self._payment_country_code = payment_country_code.upper()
        self._reconciliation_engine: PaymentReconciliationEngine | None = None

    def add_product(self, *, product_id: str, tenant_id: str, title: str, price: Decimal, currency: str, description: str = "", capability_ids: list[str] | None = None, metadata: dict[str, str] | None = None, type: ProductType | None = None, product_type: ProductType | None = None, sku: str | None = None) -> Product:
        resolved_type = type or product_type
        if resolved_type is None:
            raise ValueError("type is required")
        resolved_metadata = metadata or {}
        resolved_capability_ids = capability_ids or []
        if not resolved_capability_ids and resolved_metadata.get("capability_id"):
            resolved_capability_ids = [resolved_metadata["capability_id"]]
        return self.catalog.create_product(
            product_id=product_id,
            tenant_id=tenant_id,
            type=resolved_type,
            title=title,
            description=description,
            price=price,
            currency=currency,
            capability_ids=resolved_capability_ids,
            metadata=resolved_metadata,
            sku=sku,
        )

    def create_bundle(self, *, bundle_id: str, tenant_id: str, product_ids: list[str], pricing_rule: str, bundle_price: Decimal | None = None) -> Bundle:
        return self.catalog.create_bundle(
            Bundle(bundle_id=bundle_id, tenant_id=tenant_id, product_ids=tuple(product_ids), pricing_rule=pricing_rule, bundle_price=bundle_price)
        )

    def _resolve_product_amount(self, product: Product) -> Decimal:
        if product.type == ProductType.BUNDLE:
            bundle = self.catalog.get_bundle(product.product_id)
            if bundle and bundle.bundle_price is not None:
                return bundle.bundle_price
        return self.monetization.quote_product_amount(product)

    def _execute_payment(self, tenant_id: str, learner_id: str, amount: Decimal, currency: str, attempt: int, idempotency_key: str) -> tuple[bool, str | None, bool]:
        config = self.config_service.resolve(
            ConfigResolutionContext(tenant_id=tenant_id, country_code=self._payment_country_code, segment_id="academy")
        )
        max_attempts = int(config.behavior_tuning.get("commerce.checkout.max_payment_retries", 2)) + 1
        if attempt >= max_attempts:
            return False, None, False

        country_code = "PK" if currency.upper() == "PKR" else self._payment_country_code
        entry = self._payment_orchestrator.process_checkout_payment(
            idempotency_key=f"{tenant_id}:{learner_id}:{idempotency_key}:{attempt}",
            tenant=TenantPaymentContext(tenant_id=tenant_id, country_code=country_code),
            amount=int(amount * 100),
            currency=currency,
        )
        if entry.status in {"pending", "success"} and entry.payment_id:
            return True, entry.payment_id, False
        return False, None, bool(entry.error and "timeout" in entry.error.lower())

    async def checkout_and_invoice(self, *, session_id: str, tenant_id: str, learner_id: str, product_id: str, idempotency_key: str) -> tuple[Order, InvoiceRecord]:
        self.checkout.start_session(session_id=session_id, tenant_id=tenant_id, learner_id=learner_id, product_id=product_id, idempotency_key=idempotency_key)
        order = await self.checkout.submit_session(session_id=session_id)
        if order.status not in {OrderStatus.PAID, OrderStatus.RECONCILED}:
            raise ValueError(f"cannot invoice unpaid order '{order.order_id}'")
        invoice = self.billing.create_invoice_for_order(order)
        order = self.checkout.reconcile_order(order_id=order.order_id)
        if invoice.invoice_type == "subscription":
            plan_id = self.catalog.get_product(product_id).metadata.get("plan_id", "pro")
            self.subscription_service.create_or_activate_subscription(
                tenant_id=tenant_id,
                subscription_id=f"sub_{tenant_id}_{product_id}",
                plan_type=plan_id,
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

    def configure_reconciliation(self, engine: PaymentReconciliationEngine) -> None:
        self._reconciliation_engine = engine

    def apply_reconciliation(self, *, order_id: str, invoice_id: str, payment_id: str, resolved: bool) -> None:
        order = self.checkout.get_order(order_id)
        if order is None:
            raise KeyError("order not found")
        invoice = self.billing.get_invoice(invoice_id)
        if invoice is None:
            raise KeyError("invoice not found")
        if resolved:
            self.checkout.reconcile_order(order_id=order_id)
            updated_invoice = InvoiceRecord(
                invoice_id=invoice.invoice_id,
                user_id=invoice.user_id,
                order_id=invoice.order_id,
                amount=invoice.amount,
                status=InvoiceStatus.PAID,
                currency=invoice.currency,
                invoice_type=invoice.invoice_type,
                ledger_entry_id=invoice.ledger_entry_id,
            )
        else:
            self.checkout._orders[order_id] = Order(**{**order.__dict__, "status": OrderStatus.FAILED})
            if order.transaction_id:
                txn = self.checkout._transactions[order.transaction_id]
                self.checkout._transactions[order.transaction_id] = Transaction(**{**txn.__dict__, "status": TransactionStatus.FAILED})
            updated_invoice = InvoiceRecord(
                invoice_id=invoice.invoice_id,
                user_id=invoice.user_id,
                order_id=invoice.order_id,
                amount=invoice.amount,
                status=InvoiceStatus.OVERDUE,
                currency=invoice.currency,
                invoice_type=invoice.invoice_type,
                ledger_entry_id=invoice.ledger_entry_id,
            )
        self.billing._invoices[invoice_id] = updated_invoice

    def schedule_reconciliation_job(self) -> None:
        if self._reconciliation_engine is None:
            raise RuntimeError("reconciliation engine not configured")
        self._reconciliation_engine.schedule_periodic_reconciliation()


def build_commerce_service_for_pakistan(default_provider: str = "jazzcash") -> CommerceService:
    from integrations.payments.orchestration import build_pakistan_payment_orchestration

    return CommerceService(
        payment_orchestrator=build_pakistan_payment_orchestration(default_provider=default_provider),
        payment_country_code="PK",
    )
