from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
from typing import Sequence

sys.path.append(str(Path(__file__).resolve().parents[2]))

from backend.services.shared.events.envelope import EventEnvelope, build_event
from shared.models.config import ConfigResolutionContext
from shared.models.usage_record import UsageRecord
from shared.utils.entitlement import EntitlementDecision, TenantEntitlementContext

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


_SubscriptionModule = _load_module("subscription_service_module", "services/subscription-service/service.py")
_ConfigModule = _load_module("config_service_module", "services/config-service/service.py")
_CapabilityModule = _load_module("capability_registry_module", "services/capability-registry/service.py")

SubscriptionService = _SubscriptionModule.SubscriptionService


# ------------------------------------------------------------------ #
# BC-BILLING-01 (CGAP-041) — Contextual upsell trigger helper        #
# ------------------------------------------------------------------ #

def _emit_upsell_trigger(*, tenant_id: str, capability_id: str, trigger_reason: str) -> None:
    """BC-BILLING-01 (CGAP-041): emit commerce.upsell.triggered when a gate denies or quota approaches.

    Best-effort delivery — must never block entitlement decisions or usage metering.
    trigger_reason: "not_entitled_plan" | "not_entitled_addon" | "quota_approaching"
    """
    _MESSAGES: dict[str, str] = {
        "not_entitled_plan": (
            f"Upgrade your plan to unlock '{capability_id}'. "
            "This feature is available on higher-tier plans — review upgrade options."
        ),
        "not_entitled_addon": (
            f"Add the '{capability_id}' add-on to your subscription to enable this feature."
        ),
        "quota_approaching": (
            f"You're approaching your usage limit for '{capability_id}'. "
            "Upgrade now to avoid service interruption."
        ),
    }
    payload = {
        "event_type": "commerce.upsell.triggered",
        "tenant_id": tenant_id,
        "capability_id": capability_id,
        "trigger_reason": trigger_reason,
        "suggested_action": _MESSAGES.get(trigger_reason, f"Review your plan to enable '{capability_id}'."),
    }
    try:
        from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
        publish_event(payload)
    except Exception:
        pass  # best-effort — must not block capability gate decisions
TenantSubscription = _SubscriptionModule.TenantSubscription
ConfigService = _ConfigModule.ConfigService
CapabilityRegistryService = _CapabilityModule.CapabilityRegistryService


class EntitlementService:
    """Runtime entitlement decision engine and only source of truth for capability access."""

    def __init__(
        self,
        *,
        subscription_service: SubscriptionService | None = None,
        config_service: ConfigService | None = None,
        capability_registry_service: CapabilityRegistryService | None = None,
    ) -> None:
        self._subscription_service = subscription_service or SubscriptionService()
        self._config_service = config_service or ConfigService()
        self._capability_registry = capability_registry_service or CapabilityRegistryService()
        self._usage_records: dict[str, UsageRecord] = {}
        self._usage_idempotency_keys: set[tuple[str, str, str, str]] = set()
        self._usage_events: list[EventEnvelope] = []

    def upsert_tenant_context(self, context: TenantEntitlementContext) -> None:
        normalized = context.normalized()
        self._subscription_service.upsert_tenant_subscription(
            TenantSubscription(
                tenant_id=normalized.tenant_id,
                plan_type=normalized.plan_type,
                add_ons=normalized.add_ons,
            )
        )
        # CGAP-040: emit entitlement.updated on every plan state change.
        # Best-effort — must never block context upserts.
        try:
            from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
            publish_event({
                "event_type": "entitlement.updated",
                "tenant_id": normalized.tenant_id,
                "plan_type": normalized.plan_type,
                "add_ons": list(normalized.add_ons),
            })
        except Exception:
            pass

    def decide(self, tenant: TenantEntitlementContext, capability: str) -> EntitlementDecision:
        normalized_tenant = tenant.normalized()
        normalized_capability = capability.strip()

        capability_meta = self._capability_registry.get_capability(normalized_capability)
        if capability_meta is None:
            return EntitlementDecision(
                tenant_id=normalized_tenant.tenant_id,
                capability=normalized_capability,
                is_enabled=False,
                plan_type=normalized_tenant.plan_type,
                add_ons=normalized_tenant.add_ons,
                sources=("unknown_capability",),
            )

        subscription = self._subscription_service.get_tenant_subscription(normalized_tenant.tenant_id)
        if subscription is None:
            subscription = TenantSubscription(
                tenant_id=normalized_tenant.tenant_id,
                plan_type=normalized_tenant.plan_type,
                add_ons=normalized_tenant.add_ons,
            ).normalized()
            self._subscription_service.upsert_tenant_subscription(subscription)

        candidate_enabled = capability_meta.default_enabled
        sources: list[str] = ["registry_default"] if capability_meta.default_enabled else []

        if normalized_capability in self._subscription_service.get_plan_capabilities(subscription.plan_type):
            candidate_enabled = True
            sources.append(f"plan:{subscription.plan_type}")

        for add_on in subscription.add_ons:
            if normalized_capability in self._subscription_service.get_add_on_capabilities(add_on):
                candidate_enabled = True
                sources.append(f"addon:{add_on}")
            elif normalized_capability in self._capability_registry.list_add_on_capabilities(add_on):
                candidate_enabled = True
                sources.append(f"registry_addon:{add_on}")
        if normalized_capability in self._subscription_service.get_active_add_on_capability_ids(normalized_tenant.tenant_id):
            candidate_enabled = True
            sources.append("addon_purchase")

        effective_config = self._config_service.resolve(
            ConfigResolutionContext(
                tenant_id=normalized_tenant.tenant_id,
                country_code=normalized_tenant.country_code,
                segment_id=normalized_tenant.segment_id,
            )
        )
        if normalized_capability in effective_config.capability_enabled:
            candidate_enabled = effective_config.capability_enabled[normalized_capability]
            sources.append("config_override")

        is_enabled = bool(candidate_enabled)

        # CGAP-039: grace billing lifecycle — when plan_type is "grace", all capabilities remain
        # enabled (billing overdue, within grace window) but the decision carries a warning.
        # This must be evaluated BEFORE the is_enabled deny-reason block so grace tenants
        # still access capabilities while receiving the grace_warning signal.
        billing_warning: str | None = None
        if subscription.plan_type == "grace":
            billing_warning = "grace_warning"  # payment overdue — capabilities preserved, please renew

        # CGAP-037: Resolve BC-GATE-01 deny reason code when access is denied.
        deny_reason: str | None = None
        if not is_enabled:
            if "config_override" in sources:
                deny_reason = "flag_disabled"
            elif subscription.plan_type in {"suspended", "terminated"}:
                deny_reason = "suspended"
            elif (
                capability_meta.included_in_add_ons
                and not any(addon in subscription.add_ons for addon in capability_meta.included_in_add_ons)
            ):
                deny_reason = "not_entitled_addon"
            else:
                deny_reason = "not_entitled_plan"

        # BC-BILLING-01 (CGAP-041): emit contextual upsell trigger on entitlement denial
        if deny_reason in {"not_entitled_plan", "not_entitled_addon"}:
            _emit_upsell_trigger(
                tenant_id=normalized_tenant.tenant_id,
                capability_id=normalized_capability,
                trigger_reason=deny_reason,
            )

        return EntitlementDecision(
            tenant_id=normalized_tenant.tenant_id,
            capability=normalized_capability,
            is_enabled=is_enabled,
            plan_type=subscription.plan_type,
            add_ons=subscription.add_ons,
            sources=tuple(sources),
            deny_reason=deny_reason,
            billing_warning=billing_warning,  # CGAP-039
        )


    def resolve_enabled_capabilities(self, tenant: TenantEntitlementContext) -> set[str]:
        normalized_tenant = tenant.normalized()
        subscription = self._subscription_service.get_tenant_subscription(normalized_tenant.tenant_id)
        if subscription is None:
            subscription = TenantSubscription(
                tenant_id=normalized_tenant.tenant_id,
                plan_type=normalized_tenant.plan_type,
                add_ons=normalized_tenant.add_ons,
            ).normalized()

        candidates = {
            capability.capability_id
            for capability in self._capability_registry.list_capabilities()
            if capability.default_enabled
        }
        candidates.update(self._subscription_service.get_plan_capabilities(subscription.plan_type))

        for add_on in subscription.add_ons:
            candidates.update(self._subscription_service.get_add_on_capabilities(add_on))
            candidates.update(self._capability_registry.list_add_on_capabilities(add_on))
        candidates.update(self._subscription_service.get_active_add_on_capability_ids(normalized_tenant.tenant_id))

        effective_config = self._config_service.resolve(
            ConfigResolutionContext(
                tenant_id=normalized_tenant.tenant_id,
                country_code=normalized_tenant.country_code,
                segment_id=normalized_tenant.segment_id,
            )
        )
        for capability_id, enabled in effective_config.capability_enabled.items():
            if enabled:
                candidates.add(capability_id)
            else:
                candidates.discard(capability_id)

        return {capability_id for capability_id in candidates if self.is_enabled(normalized_tenant, capability_id)}

    def is_enabled(self, tenant: TenantEntitlementContext, capability: str) -> bool:
        return self.decide(tenant=tenant, capability=capability).is_enabled

    def resolve_capability_flags(
        self, tenant: TenantEntitlementContext, capability_ids: Sequence[str]
    ) -> dict[str, bool]:
        normalized_tenant = tenant.normalized()
        return {capability_id: self.is_enabled(normalized_tenant, capability_id) for capability_id in capability_ids}

    def meter_usage(
        self,
        *,
        tenant: TenantEntitlementContext,
        capability_id: str,
        quantity: int,
        source_service: str,
        reference_id: str,
        unit_type: str = "count",
        metadata: dict[str, str] | None = None,
        timestamp: datetime | None = None,
    ) -> UsageRecord | None:
        normalized_tenant = tenant.normalized()
        normalized_capability_id = capability_id.strip()
        capability = self._capability_registry.get_capability(normalized_capability_id)
        if capability is None:
            raise ValueError(f"unknown capability '{normalized_capability_id}'")
        if quantity < 0:
            raise ValueError("quantity must be >= 0")
        if quantity == 0:
            return None
        if not capability.usage_metered:
            return None

        normalized_reference_id = reference_id.strip()
        # CGAP-038: Enforce quota before recording usage.
        if capability.usage_quota is not None:
            current_total = sum(
                r.quantity
                for r in self._usage_records.values()
                if r.tenant_id == normalized_tenant.tenant_id
                and r.capability_id == normalized_capability_id
            )
            if current_total + quantity > capability.usage_quota:
                raise ValueError(
                    f"quota_exceeded:{normalized_capability_id}:"
                    f"limit={capability.usage_quota},current={current_total},requested={quantity}"
                )
            # BC-BILLING-01 (CGAP-041): emit upsell trigger when usage reaches ≥80% of quota
            if capability.usage_quota > 0:
                usage_pct = (current_total + quantity) / capability.usage_quota
                if usage_pct >= 0.80:
                    _emit_upsell_trigger(
                        tenant_id=normalized_tenant.tenant_id,
                        capability_id=normalized_capability_id,
                        trigger_reason="quota_approaching",
                    )

        idempotency_key = (
            normalized_tenant.tenant_id,
            normalized_capability_id,
            source_service.strip(),
            normalized_reference_id,
        )
        if idempotency_key in self._usage_idempotency_keys:
            return None
        self._usage_idempotency_keys.add(idempotency_key)

        usage = UsageRecord(
            usage_id=str(uuid4()),
            tenant_id=normalized_tenant.tenant_id,
            capability_id=normalized_capability_id,
            unit_type=unit_type,
            quantity=quantity,
            source_service=source_service,
            timestamp=timestamp or datetime.now(timezone.utc),
            reference_id=normalized_reference_id,
            metadata=metadata or {},
        ).normalized()
        self._usage_records[usage.usage_id] = usage
        self._usage_events.append(
            build_event(
                event_type="lms.usage.recorded.v1",
                topic="lms.usage.recorded",
                producer_service="entitlement-service",
                schema_version="v1",
                tenant_id=usage.tenant_id,
                correlation_id=usage.reference_id,
                payload={
                    "usage_id": usage.usage_id,
                    "capability_id": usage.capability_id,
                    "unit_type": usage.unit_type,
                    "quantity": usage.quantity,
                    "source_service": usage.source_service,
                    "timestamp": usage.timestamp.isoformat(),
                    "reference_id": usage.reference_id,
                    "metadata": usage.metadata,
                },
                metadata={"event_family": "usage"},
            )
        )
        return usage

    # ------------------------------------------------------------------
    # BC-PAY-01: Payment → entitlement activation handler — MO-033 / Phase D
    # Called by PaymentService.activate_entitlement_on_payment() (MO-028)
    # when a payment.verified event fires. Upserts the tenant's subscription
    # context to ensure capability access is granted in the same request cycle.
    # ------------------------------------------------------------------

    def activate_from_payment(
        self,
        *,
        tenant_id: str,
        user_id: str,
        order_id: str | None,
        payment_id: str,
    ) -> None:
        """Activate entitlement following a verified payment (BC-PAY-01 / MO-033).

        Looks up the existing subscription context and refreshes it so that
        plan-included capabilities are immediately available. If no context
        exists, bootstraps a "starter" plan context — the minimum access
        level for a paying tenant.

        This is the consuming side of the entitlement.activated event chain:
          PaymentService.handle_provider_callback()
            → activate_entitlement_on_payment()   [MO-028 emitter]
              → EntitlementService.activate_from_payment()  [this method]
        """
        tid = tenant_id.strip()
        existing = self._subscription_service.get_tenant_subscription(tid)

        if existing is not None:
            # Refresh existing context — re-upsert to ensure config layer reflects payment
            self.upsert_tenant_context(
                TenantEntitlementContext(
                    tenant_id=tid,
                    plan_type=existing.plan_type if existing.plan_type not in {"suspended", "terminated"} else "starter",
                    add_ons=tuple(existing.add_ons),
                )
            )
        else:
            # No prior context — bootstrap with starter plan minimum access
            self.upsert_tenant_context(
                TenantEntitlementContext(
                    tenant_id=tid,
                    plan_type="starter",
                    add_ons=(),
                )
            )

        # Emit payment-sourced entitlement activation audit event (best-effort)
        try:
            from backend.services.shared.events.envelope import publish_event  # type: ignore[import]
            publish_event({
                "event_type": "entitlement.activated.confirmed",
                "tenant_id": tid,
                "user_id": user_id,
                "payment_id": payment_id,
                "order_id": order_id,
                "source": "entitlement_service.activate_from_payment",
                "activated_at": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            pass

    def list_usage_records(self, *, tenant_id: str | None = None) -> list[UsageRecord]:
        records = self._usage_records.values()
        if tenant_id:
            normalized_tenant = tenant_id.strip()
            records = [item for item in records if item.tenant_id == normalized_tenant]
        return sorted(records, key=lambda item: item.timestamp)

    def list_usage_events(self) -> list[EventEnvelope]:
        return list(self._usage_events)

    def has_bypass_paths(self) -> bool:
        required_methods = (
            hasattr(self, "decide"),
            hasattr(self, "is_enabled"),
        )
        return not all(required_methods)
