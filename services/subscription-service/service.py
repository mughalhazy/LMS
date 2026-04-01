from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import importlib.util
from typing import Callable

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from services.commerce.billing import BillingService, InvoiceRecord
from services.commerce.models import SubscriptionPlan
from shared.models.plan import Plan
from shared.models.addon import AddOn
from shared.models.capability_pricing import CapabilityPricing

_ROOT = Path(__file__).resolve().parents[2]


def _load_registry_service():
    module_path = _ROOT / "services/capability-registry/service.py"
    sys.path.append(str(module_path.parent))
    spec = importlib.util.spec_from_file_location("capability_registry_for_subscription", module_path)
    if spec is None or spec.loader is None:
        raise ImportError("Unable to load capability registry service")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.CapabilityRegistryService


@dataclass(frozen=True)
class TenantSubscription:
    tenant_id: str
    plan_type: str
    add_ons: tuple[str, ...] = field(default_factory=tuple)

    def normalized(self) -> "TenantSubscription":
        return TenantSubscription(
            tenant_id=self.tenant_id.strip(),
            plan_type=self.plan_type.strip().lower(),
            add_ons=tuple(sorted({addon.strip().lower() for addon in self.add_ons if addon.strip()})),
        )


@dataclass(frozen=True)
class CommerceSubscription:
    subscription_id: str
    tenant_id: str
    plan_type: str
    source_order_id: str
    plan_id: str = ""
    status: str = "active"
    renewals: int = 0


@dataclass(frozen=True)
class TenantAddOnAttachment:
    tenant_id: str
    addon_id: str
    capability_id: str
    status: str = "active"


class SubscriptionService:
    """Source of truth for tenant subscription packaging (plan and add-ons)."""

    def __init__(self) -> None:
        self._tenant_subscriptions: dict[str, TenantSubscription] = {}
        self._tenant_add_on_purchases: dict[str, set[str]] = {}
        self._tenant_add_on_attachments: dict[str, dict[str, TenantAddOnAttachment]] = {}
        self._add_on_catalog: dict[str, AddOn] = {}
        self._add_on_activation_audit_log: list[dict[str, str]] = []
        self._tenant_usage_ledger: dict[str, dict[str, int]] = {}
        self._commerce_subscriptions: dict[str, CommerceSubscription] = {}
        self._subscription_plans: dict[str, SubscriptionPlan] = {}
        self._plan_catalog: dict[str, Plan] = {}
        self._billing = BillingService()
        self._subscription_invoices: dict[str, list[InvoiceRecord]] = {}
        self._capability_registry = _load_registry_service()()
        self._bootstrap_plan_catalog()
        self._bootstrap_add_on_catalog()

    def _bootstrap_plan_catalog(self) -> None:
        default_plans = (
            Plan(
                plan_id="free",
                name="Free",
                billing_cycle="monthly",
                included_capability_ids=("assessment.attempt", "commerce.catalog.basic", "learning.analytics.basic",
                    "recommendation.basic"),
                addon_eligible_capability_ids=("ai.tutor", "learning.analytics.advanced"),
                usage_limits={"assessment.attempt": 200},
                country_defaults={"US": "free", "PK": "starter_academy"},
                segment_defaults={"academy": "starter_academy"},
            ),
            Plan(
                plan_id="pro",
                name="Pro",
                billing_cycle="monthly",
                included_capability_ids=(
                    "assessment.attempt",
                    "assessment.author",
                    "commerce.catalog.basic",
                    "course.write",
                    "learning.analytics.basic",
                    "recommendation.basic",
                ),
                addon_eligible_capability_ids=("ai.tutor", "learning.analytics.advanced", "platform.support.priority"),
                usage_limits={"assessment.attempt": 5000},
                country_defaults={"US": "pro", "PK": "growth_academy"},
                segment_defaults={"academy": "growth_academy"},
            ),
            Plan(
                plan_id="enterprise",
                name="Enterprise",
                billing_cycle="yearly",
                included_capability_ids=(
                    "assessment.attempt",
                    "assessment.author",
                    "commerce.catalog.basic",
                    "course.write",
                    "learning.analytics.basic",
                    "learning.analytics.advanced",
                    "platform.support.priority",
                    "recommendation.basic",
                ),
                addon_eligible_capability_ids=("ai.tutor", "platform.isolation.dedicated"),
                usage_limits={"assessment.attempt": 100000},
                country_defaults={"US": "enterprise", "PK": "enterprise_learning"},
                segment_defaults={"school": "enterprise_learning", "enterprise": "enterprise_learning"},
            ),
            Plan(
                plan_id="starter_academy",
                name="Starter Academy",
                billing_cycle="monthly",
                included_capability_ids=(
                    "assessment.attempt",
                    "learning.analytics.basic",
                    "attendance_tracking",
                    "manual_payment",
                ),
                addon_eligible_capability_ids=("parent_notifications", "cohort_management"),
                usage_limits={"assessment.attempt": 1000},
                country_defaults={"PK": "starter_academy"},
                segment_defaults={"academy": "starter_academy"},
            ),
            Plan(
                plan_id="growth_academy",
                name="Growth Academy",
                billing_cycle="monthly",
                included_capability_ids=(
                    "assessment.attempt",
                    "assessment.author",
                    "course.write",
                    "attendance_tracking",
                    "cohort_management",
                    "fee_tracking",
                    "installment_billing",
                    "manual_payment",
                    "parent_notifications",
                    "teacher_dashboard",
                    "teacher_assignment",
                    "timetable_scheduling",
                ),
                addon_eligible_capability_ids=("exam_engine", "owner_analytics", "offline_learning"),
                usage_limits={"assessment.attempt": 10000},
                country_defaults={"PK": "growth_academy"},
                segment_defaults={"academy": "growth_academy"},
            ),
            Plan(
                plan_id="school_basic",
                name="School Basic",
                billing_cycle="monthly",
                included_capability_ids=(
                    "assessment.attempt",
                    "attendance_tracking",
                    "cohort_management",
                    "parent_notifications",
                    "timetable_scheduling",
                ),
                addon_eligible_capability_ids=("fee_tracking", "manual_payment", "installment_billing", "teacher_dashboard"),
                usage_limits={"assessment.attempt": 3000},
                country_defaults={"PK": "school_basic"},
                segment_defaults={"school": "school_basic"},
            ),
            Plan(
                plan_id="enterprise_learning",
                name="Enterprise Learning",
                billing_cycle="yearly",
                included_capability_ids=(
                    "assessment.attempt",
                    "assessment.author",
                    "course.write",
                    "attendance_tracking",
                    "cohort_management",
                    "exam_engine",
                    "fee_tracking",
                    "installment_billing",
                    "manual_payment",
                    "offline_learning",
                    "operations_dashboard",
                    "owner_analytics",
                    "parent_notifications",
                    "platform.isolation.dedicated",
                    "platform.support.priority",
                    "secure_media_delivery",
                    "student_lifecycle_management",
                    "teacher_assignment",
                    "teacher_dashboard",
                    "teacher_revenue_sharing",
                    "timetable_scheduling",
                    "whatsapp_primary_interface",
                    "whatsapp_workflows",
                ),
                addon_eligible_capability_ids=("ai.tutor",),
                usage_limits={"assessment.attempt": 50000, "offline_learning": 25000},
                country_defaults={"PK": "enterprise_learning"},
                segment_defaults={"academy": "enterprise_learning", "enterprise": "enterprise_learning"},
            ),
        )
        for plan in default_plans:
            self.upsert_plan(plan)

    def _bootstrap_add_on_catalog(self) -> None:
        defaults = (
            AddOn(
                addon_id="whatsapp_workflows",
                capability_id="whatsapp_workflows",
                price=Decimal("39.00"),
                billing_mode="recurring",
                eligibility_rules={"segments": ("academy", "school", "enterprise")},
                country_scope=("PK",),
                status="active",
            ),
            AddOn(
                addon_id="installment_billing",
                capability_id="installment_billing",
                price=Decimal("29.00"),
                billing_mode="recurring",
                eligibility_rules={"segments": ("academy", "school", "enterprise")},
                country_scope=("PK",),
                status="active",
            ),
            AddOn(
                addon_id="advanced_secure_media",
                capability_id="advanced_secure_media",
                price=Decimal("59.00"),
                billing_mode="recurring",
                eligibility_rules={"segments": ("academy", "enterprise")},
                country_scope=("PK", "US"),
                status="active",
            ),
            AddOn(
                addon_id="owner_analytics",
                capability_id="owner_analytics",
                price=Decimal("49.00"),
                billing_mode="usage_based",
                eligibility_rules={"segments": ("academy", "enterprise")},
                country_scope=("PK",),
                status="active",
            ),
            AddOn(
                addon_id="ai_tutor",
                capability_id="ai.tutor",
                price=Decimal("79.00"),
                billing_mode="usage_based",
                eligibility_rules={"segments": ("academy", "school", "enterprise")},
                country_scope=("PK", "US"),
                status="active",
            ),
            AddOn(
                addon_id="ai_tutor_pack",
                capability_id="ai.tutor",
                price=Decimal("79.00"),
                billing_mode="usage_based",
                eligibility_rules={"segments": ("academy", "school", "enterprise", "smb")},
                country_scope=("PK", "US"),
                status="active",
            ),
            AddOn(
                addon_id="learning_analytics_advanced",
                capability_id="learning.analytics.advanced",
                price=Decimal("0.10"),
                billing_mode="usage_based",
                eligibility_rules={"segments": ("academy", "school", "enterprise")},
                country_scope=("PK", "US"),
                status="active",
            ),
            AddOn(
                addon_id="analytics_advanced",
                capability_id="learning.analytics.advanced",
                price=Decimal("0.10"),
                billing_mode="usage_based",
                eligibility_rules={"segments": ("academy", "school", "enterprise", "smb")},
                country_scope=("PK", "US"),
                status="active",
            ),
        )
        for add_on in defaults:
            self.upsert_add_on(add_on)

    def upsert_add_on(self, add_on: AddOn) -> None:
        normalized = add_on.normalized()
        self._add_on_catalog[normalized.addon_id] = normalized

    def list_eligible_add_ons(
        self,
        *,
        tenant_id: str,
        country_code: str,
        segment_id: str,
    ) -> list[AddOn]:
        subscription = self.get_tenant_subscription(tenant_id)
        if subscription is None:
            return []
        eligible_capabilities = self.get_plan_addon_eligible_capabilities(subscription.plan_type)
        normalized_country = country_code.strip().upper()
        normalized_segment = segment_id.strip().lower()
        eligible_add_ons: list[AddOn] = []
        for add_on in self._add_on_catalog.values():
            if add_on.status != "active":
                continue
            if add_on.capability_id not in eligible_capabilities:
                continue
            if add_on.country_scope and normalized_country not in add_on.country_scope:
                continue
            segments = add_on.eligibility_rules.get("segments", ())
            if segments and normalized_segment not in segments:
                continue
            eligible_add_ons.append(add_on)
        return sorted(eligible_add_ons, key=lambda item: item.addon_id)

    def purchase_add_on(
        self,
        *,
        tenant_id: str,
        addon_id: str,
        actor_id: str = "system",
    ) -> TenantAddOnAttachment:
        normalized_tenant_id = tenant_id.strip()
        normalized_addon_id = addon_id.strip().lower()
        add_on = self._add_on_catalog.get(normalized_addon_id)
        if add_on is None:
            raise ValueError(f"unknown add-on '{normalized_addon_id}'")
        attachment = self.attach_add_on_to_tenant_subscription(
            tenant_id=normalized_tenant_id,
            addon_id=normalized_addon_id,
        )
        self.activate_add_on(
            tenant_id=normalized_tenant_id,
            addon_id=normalized_addon_id,
            actor_id=actor_id,
        )
        return attachment

    def upsert_plan(self, plan: Plan) -> None:
        normalized = plan.normalized()
        self._plan_catalog[normalized.plan_id] = normalized

    def get_plan(self, plan_id: str) -> Plan | None:
        return self._plan_catalog.get(plan_id.strip().lower())

    def upsert_tenant_subscription(self, subscription: TenantSubscription) -> None:
        normalized = subscription.normalized()
        self._tenant_subscriptions[normalized.tenant_id] = normalized

    def get_tenant_subscription(self, tenant_id: str) -> TenantSubscription | None:
        return self._tenant_subscriptions.get(tenant_id.strip())

    def purchase_capability_add_on(self, tenant_id: str, capability_id: str) -> None:
        normalized_tenant_id = tenant_id.strip()
        normalized_capability_id = capability_id.strip()
        for add_on in self._add_on_catalog.values():
            if add_on.capability_id == normalized_capability_id and add_on.status == "active":
                self.purchase_add_on(
                    tenant_id=normalized_tenant_id,
                    addon_id=add_on.addon_id,
                    actor_id="commerce.purchase_capability_add_on",
                )
                return
        subscription = self.get_tenant_subscription(normalized_tenant_id)
        if subscription is not None:
            eligible = self.get_plan_addon_eligible_capabilities(subscription.plan_type)
            if eligible and normalized_capability_id not in eligible:
                raise ValueError(
                    f"capability '{normalized_capability_id}' is not eligible as an add-on for plan '{subscription.plan_type}'"
                )
        purchased = self._tenant_add_on_purchases.setdefault(normalized_tenant_id, set())
        purchased.add(normalized_capability_id)

    def get_purchased_capability_add_ons(self, tenant_id: str) -> set[str]:
        return set(self._tenant_add_on_purchases.get(tenant_id.strip(), set()))

    def record_capability_usage(self, *, tenant_id: str, capability_id: str, units: int = 1) -> None:
        normalized_tenant_id = tenant_id.strip()
        normalized_capability_id = capability_id.strip()
        ledger = self._tenant_usage_ledger.setdefault(normalized_tenant_id, {})
        ledger[normalized_capability_id] = ledger.get(normalized_capability_id, 0) + max(units, 0)

    def get_usage_for_tenant(self, tenant_id: str) -> dict[str, int]:
        return dict(self._tenant_usage_ledger.get(tenant_id.strip(), {}))

    def calculate_capability_charge(
        self,
        *,
        tenant_id: str,
        pricing: CapabilityPricing,
    ) -> Decimal:
        normalized_pricing = pricing.normalized()
        if normalized_pricing.usage_based:
            units = self._tenant_usage_ledger.get(tenant_id.strip(), {}).get(normalized_pricing.capability_id, 0)
            return normalized_pricing.price * Decimal(units)
        return normalized_pricing.price

    def get_plan_capabilities(self, plan_type: str) -> set[str]:
        normalized_plan = plan_type.strip().lower()
        plan = self.get_plan(normalized_plan)
        if plan is None:
            return set()
        return set(plan.included_capability_ids)

    def get_plan_addon_eligible_capabilities(self, plan_type: str) -> set[str]:
        plan = self.get_plan(plan_type)
        if plan is None:
            return set()
        return set(plan.addon_eligible_capability_ids)

    def attach_add_on_to_tenant_subscription(self, *, tenant_id: str, addon_id: str) -> TenantAddOnAttachment:
        normalized_tenant_id = tenant_id.strip()
        normalized_addon_id = addon_id.strip().lower()
        add_on = self._add_on_catalog.get(normalized_addon_id)
        if add_on is None:
            raise ValueError(f"unknown add-on '{normalized_addon_id}'")
        attachments = self._tenant_add_on_attachments.setdefault(normalized_tenant_id, {})
        existing = attachments.get(normalized_addon_id)
        if existing and existing.status == "active":
            raise ValueError(f"duplicate add-on purchase not allowed for '{normalized_addon_id}'")
        attachment = TenantAddOnAttachment(
            tenant_id=normalized_tenant_id,
            addon_id=normalized_addon_id,
            capability_id=add_on.capability_id,
            status="active",
        )
        attachments[normalized_addon_id] = attachment
        purchased = self._tenant_add_on_purchases.setdefault(normalized_tenant_id, set())
        purchased.add(add_on.capability_id)
        return attachment

    def activate_add_on(self, *, tenant_id: str, addon_id: str, actor_id: str) -> None:
        normalized_tenant_id = tenant_id.strip()
        normalized_addon_id = addon_id.strip().lower()
        attachments = self._tenant_add_on_attachments.get(normalized_tenant_id, {})
        attachment = attachments.get(normalized_addon_id)
        if attachment is None:
            raise ValueError(f"add-on '{normalized_addon_id}' is not attached")
        attachments[normalized_addon_id] = TenantAddOnAttachment(
            tenant_id=attachment.tenant_id,
            addon_id=attachment.addon_id,
            capability_id=attachment.capability_id,
            status="active",
        )
        self._add_on_activation_audit_log.append(
            {
                "tenant_id": normalized_tenant_id,
                "addon_id": normalized_addon_id,
                "capability_id": attachment.capability_id,
                "event": "activated",
                "actor_id": actor_id.strip() or "system",
            }
        )

    def revoke_add_on(self, *, tenant_id: str, addon_id: str, reason: str = "expired") -> None:
        normalized_tenant_id = tenant_id.strip()
        normalized_addon_id = addon_id.strip().lower()
        attachments = self._tenant_add_on_attachments.get(normalized_tenant_id, {})
        attachment = attachments.get(normalized_addon_id)
        if attachment is None:
            return
        attachments[normalized_addon_id] = TenantAddOnAttachment(
            tenant_id=attachment.tenant_id,
            addon_id=attachment.addon_id,
            capability_id=attachment.capability_id,
            status="revoked",
        )
        purchased = self._tenant_add_on_purchases.setdefault(normalized_tenant_id, set())
        purchased.discard(attachment.capability_id)
        self._add_on_activation_audit_log.append(
            {
                "tenant_id": normalized_tenant_id,
                "addon_id": normalized_addon_id,
                "capability_id": attachment.capability_id,
                "event": f"revoked:{reason.strip() or 'expired'}",
                "actor_id": "system",
            }
        )

    def get_active_add_on_capability_ids(self, tenant_id: str) -> set[str]:
        normalized_tenant_id = tenant_id.strip()
        attachments = self._tenant_add_on_attachments.get(normalized_tenant_id, {})
        return {item.capability_id for item in attachments.values() if item.status == "active"}

    def get_add_on_activation_audit_log(self, tenant_id: str) -> list[dict[str, str]]:
        normalized_tenant_id = tenant_id.strip()
        return [entry for entry in self._add_on_activation_audit_log if entry["tenant_id"] == normalized_tenant_id]

    def is_enabled_for_subscription(
        self,
        *,
        tenant_id: str = "",
        plan_type: str,
        add_ons: tuple[str, ...],
        capability: str,
        entitlement: Callable[[str], bool],
    ) -> bool:
        normalized_capability = capability.strip()
        if entitlement(normalized_capability):
            return True
        purchased = normalized_capability in self.get_purchased_capability_add_ons(tenant_id)
        if purchased:
            return True
        for add_on in add_ons:
            if normalized_capability in self.get_add_on_capabilities(add_on):
                return True
        return False

    def get_add_on_capabilities(self, add_on: str) -> set[str]:
        normalized_add_on = add_on.strip().lower()
        add_on_record = self._add_on_catalog.get(normalized_add_on)
        if add_on_record is None:
            return set()
        return {add_on_record.capability_id}

    def start_subscription(
        self,
        *,
        tenant_id: str,
        subscription_id: str,
        plan: SubscriptionPlan,
        source_order_id: str,
    ) -> CommerceSubscription:
        normalized_plan = plan.normalized()
        self._subscription_plans[normalized_plan.plan_id] = normalized_plan
        normalized = CommerceSubscription(
            subscription_id=subscription_id.strip(),
            tenant_id=tenant_id.strip(),
            plan_type=normalized_plan.plan_id,
            source_order_id=source_order_id.strip(),
            plan_id=normalized_plan.plan_id,
            status="active",
            renewals=0,
        )
        self._commerce_subscriptions[normalized.subscription_id] = normalized
        invoice = self._billing.create_recurring_charge(
            subscription_id=normalized.subscription_id,
            plan=normalized_plan,
            tenant_id=normalized.tenant_id,
        )
        self._subscription_invoices.setdefault(normalized.subscription_id, []).append(invoice)
        return normalized

    def renew_subscription(self, subscription_id: str) -> CommerceSubscription:
        current = self._commerce_subscriptions[subscription_id.strip()]
        if current.status == "canceled":
            raise ValueError("cannot renew canceled subscription")
        renewed = CommerceSubscription(
            subscription_id=current.subscription_id,
            tenant_id=current.tenant_id,
            plan_type=current.plan_type,
            source_order_id=current.source_order_id,
            plan_id=current.plan_id,
            status="active",
            renewals=current.renewals + 1,
        )
        self._commerce_subscriptions[renewed.subscription_id] = renewed
        plan = self._subscription_plans.get(renewed.plan_id or renewed.plan_type)
        if plan is not None:
            invoice = self._billing.create_recurring_charge(
                subscription_id=renewed.subscription_id,
                plan=plan,
                tenant_id=renewed.tenant_id,
            )
            self._subscription_invoices.setdefault(renewed.subscription_id, []).append(invoice)
        return renewed

    def cancel_subscription(self, subscription_id: str) -> CommerceSubscription:
        current = self._commerce_subscriptions[subscription_id.strip()]
        canceled = CommerceSubscription(
            subscription_id=current.subscription_id,
            tenant_id=current.tenant_id,
            plan_type=current.plan_type,
            source_order_id=current.source_order_id,
            plan_id=current.plan_id,
            status="canceled",
            renewals=current.renewals,
        )
        self._commerce_subscriptions[canceled.subscription_id] = canceled
        return canceled

    def get_subscription_contract(self, subscription_id: str) -> CommerceSubscription | None:
        return self._commerce_subscriptions.get(subscription_id.strip())

    # Backward-compatible alias used by commerce service.
    def create_or_activate_subscription(
        self,
        *,
        tenant_id: str,
        subscription_id: str,
        plan_type: str,
        source_order_id: str,
    ) -> CommerceSubscription:
        return self.start_subscription(
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            plan=SubscriptionPlan(
                plan_id=plan_type,
                billing_cycle="monthly",
                price=Decimal("29.00"),
                capability_ids=tuple(sorted(self.get_plan_capabilities(plan_type))),
            ),
            source_order_id=source_order_id,
        )
