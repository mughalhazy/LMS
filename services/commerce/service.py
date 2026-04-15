from __future__ import annotations

import asyncio
import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from .billing import BillingService, InvoiceRecord, InvoiceStatus
from .catalog import CatalogService
from .checkout import CheckoutService, Order, OrderStatus, Transaction, TransactionStatus
from .models import Bundle, Product, ProductType
from .monetization import CapabilityCharge, CapabilityMonetizationService
from .owner_economics import OwnerEconomicsEngine

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
        self._teacher_revenue_share_records: list[dict[str, str]] = []
        self.owner_economics = OwnerEconomicsEngine()

    def add_product(self, *, product_id: str, tenant_id: str, title: str, price: Decimal, currency: str, description: str = "", capability_ids: list[str] | None = None, metadata: dict[str, str] | None = None, type: ProductType | None = None, product_type: ProductType | None = None, sku: str | None = None) -> Product:
        resolved_type = type or product_type
        if resolved_type is None:
            raise ValueError("type is required")
        resolved_metadata = metadata or {}
        resolved_capability_ids = capability_ids or []
        if not resolved_capability_ids and resolved_metadata.get("capability_id"):
            resolved_capability_ids = [resolved_metadata["capability_id"]]
        for capability_id in resolved_capability_ids:
            self.monetization.ensure_capability_has_pricing_path(
                capability_id=capability_id,
                country_code=resolved_metadata.get("country_code", self._payment_country_code),
                plan_id=resolved_metadata.get("plan_id", ""),
            )
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

        # MS-CONFIG-01 (MS§3.2): country_code is set at service construction time via
        # payment_country_code; no inline currency→country derivation in business logic.
        entry = self._payment_orchestrator.process_checkout_payment(
            idempotency_key=f"{tenant_id}:{learner_id}:{idempotency_key}:{attempt}",
            tenant=TenantPaymentContext(tenant_id=tenant_id, country_code=self._payment_country_code),
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
        if invoice.invoice_type.startswith("subscription"):

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

    def generate_academy_fee_invoice(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        fee_reference_id: str,
        amount: Decimal,
        fee_type: str,
        currency: str = "USD",
    ) -> InvoiceRecord:
        invoice = InvoiceRecord(
            invoice_id=f"fee_{fee_reference_id}",
            user_id=tenant_id,
            order_id=f"academy_fee:{learner_id}:{fee_reference_id}",
            amount=Decimal(amount),
            currency=currency,
            invoice_type=f"academy_fee:{fee_type}",
        )
        self.billing._invoices[invoice.invoice_id] = invoice
        return invoice

    def record_teacher_revenue_share(
        self,
        *,
        tenant_id: str,
        batch_id: str,
        teacher_id: str,
        invoice_id: str,
        revenue_amount: Decimal,
        payout_amount: Decimal,
        payment_id: str | None = None,
        ledger_entry_id: str | None = None,
    ) -> dict[str, str]:
        record = {
            "tenant_id": tenant_id,
            "batch_id": batch_id,
            "teacher_id": teacher_id,
            "invoice_id": invoice_id,
            "revenue_amount": str(Decimal(revenue_amount).quantize(Decimal("0.01"))),
            "payout_amount": str(Decimal(payout_amount).quantize(Decimal("0.01"))),
            "payment_id": payment_id or "",
            "ledger_entry_id": ledger_entry_id or "",
        }
        self._teacher_revenue_share_records.append(record)
        return record

    def enable_capability_add_on(self, *, tenant_id: str, capability_id: str, country_code: str = "", plan_id: str = "") -> None:
        self.monetization.enable_add_on(tenant_id=tenant_id, capability_id=capability_id, country_code=country_code or self._payment_country_code, plan_id=plan_id)

    def record_capability_usage(
        self,
        *,
        tenant_id: str,
        capability_id: str,
        units: int = 1,
        source_service: str = "commerce-service",
        reference_id: str | None = None,
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.monetization.usage_billing_hook(
            tenant_id=tenant_id,
            capability_id=capability_id,
            units=units,
            source_service=source_service,
            reference_id=reference_id,
            metadata=metadata,
        )

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


    def compute_owner_economics_snapshot(
        self,
        *,
        tenant_id: str,
        reporting_period: str,
        ledger_entries: tuple[object, ...],
        batches: tuple[object, ...],
        branches: tuple[object, ...],
        metadata: dict[str, str] | None = None,
    ):
        return self.owner_economics.compute_profitability_snapshot(
            tenant_id=tenant_id,
            reporting_period=reporting_period,
            ledger_entries=ledger_entries,
            commerce_invoices=tuple(self.billing._invoices.values()),
            batches=batches,
            branches=branches,
            metadata=metadata,
        )

    def schedule_reconciliation_job(self) -> None:
        if self._reconciliation_engine is None:
            raise RuntimeError("reconciliation engine not configured")
        self._reconciliation_engine.schedule_periodic_reconciliation()

    # ------------------------------------------------------------------ #
    # BC-REV-01 (CGAP-042) — Revenue anomaly detection + event emission  #
    # ------------------------------------------------------------------ #

    def detect_revenue_anomalies(
        self,
        *,
        tenant_id: str,
        prior_period_revenue: Decimal | None = None,
    ) -> tuple[dict, ...]:
        """BC-REV-01 (CGAP-042): detect revenue risk signals and emit revenue.anomaly.detected.

        Checks the 4 mandatory signal categories defined in BC-REV-01 (B3P06 §11):
        - unpaid_installment: fee/installment invoices overdue ≥7 days
        - renewal_at_risk: active subscription where latest invoice is OVERDUE
        - revenue_decline: MTD PAID revenue < prior same-period by ≥15%
        - churn_signal: ≥3 subscription cancellations in last 7 days

        Each detected anomaly is emitted as revenue.anomaly.detected via publish_event()
        (best-effort). Returns tuple of all emitted anomaly payloads.
        """
        now = datetime.now(timezone.utc)
        anomalies: list[dict] = []

        def _emit(anomaly: dict) -> None:
            anomalies.append(anomaly)
            try:
                from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
                publish_event(anomaly)
            except Exception:
                pass  # best-effort — revenue anomaly emission must not block commerce ops

        # 1. Unpaid installments overdue ≥7 days
        overdue_cutoff = now - timedelta(days=7)
        overdue_installments = [
            inv for inv in self.billing._invoices.values()
            if inv.status == InvoiceStatus.OVERDUE
            and inv.tenant_id == tenant_id
            and ("fee" in inv.invoice_type or "installment" in inv.invoice_type)
            and inv.created_at <= overdue_cutoff
        ]
        if overdue_installments:
            _emit({
                "event_type": "revenue.anomaly.detected",
                "anomaly_type": "unpaid_installment",
                "severity": "high",
                "tenant_id": tenant_id,
                "affected_entities": [inv.invoice_id for inv in overdue_installments],
                "suggested_action": (
                    f"Follow up on {len(overdue_installments)} overdue installment(s) — "
                    "contact affected learners to arrange payment or escalate to management."
                ),
            })

        # 2. Subscription renewal at risk: active subscription with latest invoice OVERDUE
        at_risk_subs: list[str] = []
        for sub_id, invoices in self.subscription_service._subscription_invoices.items():
            sub = self.subscription_service.get_subscription_contract(sub_id)
            if sub is None or sub.tenant_id != tenant_id or sub.status == "canceled":
                continue
            if invoices and invoices[-1].status == InvoiceStatus.OVERDUE:
                at_risk_subs.append(sub_id)
        if at_risk_subs:
            _emit({
                "event_type": "revenue.anomaly.detected",
                "anomaly_type": "renewal_at_risk",
                "severity": "high",
                "tenant_id": tenant_id,
                "affected_entities": at_risk_subs,
                "suggested_action": (
                    f"{len(at_risk_subs)} subscription renewal(s) have failed payment. "
                    "Retry payment or reach out to the tenant to prevent lapse."
                ),
            })

        # 3. Revenue decline: MTD PAID revenue < prior same-period by ≥15%
        curr_month, curr_year = now.month, now.year
        prior_month = curr_month - 1 if curr_month > 1 else 12
        prior_year = curr_year if curr_month > 1 else curr_year - 1

        current_mtd = sum(
            (inv.amount for inv in self.billing._invoices.values()
             if inv.status == InvoiceStatus.PAID
             and inv.tenant_id == tenant_id
             and inv.created_at.year == curr_year
             and inv.created_at.month == curr_month),
            Decimal("0"),
        )
        computed_prior = prior_period_revenue
        if computed_prior is None:
            computed_prior = sum(
                (inv.amount for inv in self.billing._invoices.values()
                 if inv.status == InvoiceStatus.PAID
                 and inv.tenant_id == tenant_id
                 and inv.created_at.year == prior_year
                 and inv.created_at.month == prior_month),
                Decimal("0"),
            )
        if computed_prior > Decimal("0"):
            decline_pct = (computed_prior - current_mtd) / computed_prior * 100
            if decline_pct >= Decimal("15"):
                _emit({
                    "event_type": "revenue.anomaly.detected",
                    "anomaly_type": "revenue_decline",
                    "severity": "medium",
                    "tenant_id": tenant_id,
                    "affected_entities": [],
                    "suggested_action": (
                        f"Month-to-date revenue is down {float(decline_pct):.1f}% vs prior period. "
                        "Review courses with declining enrollment and consider promotional actions."
                    ),
                })

        # 4. Churn signal: ≥3 subscription cancellations in last 7 days
        churn_window = now - timedelta(days=7)
        recent_cancellations = self.subscription_service.get_recent_cancellations(
            tenant_id=tenant_id,
            since=churn_window,
        )
        if len(recent_cancellations) >= 3:
            _emit({
                "event_type": "revenue.anomaly.detected",
                "anomaly_type": "churn_signal",
                "severity": "high",
                "tenant_id": tenant_id,
                "affected_entities": [c["subscription_id"] for c in recent_cancellations],
                "suggested_action": (
                    f"{len(recent_cancellations)} subscription cancellations in the past 7 days. "
                    "Investigate churn causes and initiate retention outreach immediately."
                ),
            })

        return tuple(anomalies)


def build_commerce_service_for_country(country_code: str, default_provider: str) -> CommerceService:
    """MS-CONFIG-01 (MS§3.2): country-specific commerce service via adapter substitution.

    Constructs a CommerceService with the appropriate payment orchestration adapter
    for the given country. No inline country branching inside service business logic —
    the country is set once at construction and flows through payment_country_code.
    """
    from integrations.payments.orchestration import build_pakistan_payment_orchestration
    _country = country_code.upper()
    if _country == "PK":
        orchestrator = build_pakistan_payment_orchestration(default_provider=default_provider)
    else:
        raise ValueError(
            f"No payment orchestration adapter registered for country '{_country}'. "
            "Add an adapter in integrations/payments/ and register it here."
        )
    return CommerceService(
        payment_orchestrator=orchestrator,
        payment_country_code=_country,
    )


def build_commerce_service_for_pakistan(default_provider: str = "jazzcash") -> CommerceService:
    """Backward-compatible alias — delegates to build_commerce_service_for_country()."""
    return build_commerce_service_for_country(country_code="PK", default_provider=default_provider)
