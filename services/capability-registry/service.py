from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from shared.models.capability import Capability
from shared.models.capability_pricing import CapabilityPricing

from store import capability_index, feature_capability_mapping


class CapabilityRegistryService:
    def __init__(self) -> None:
        # B2P05: dependency graph — maps capability_id → set of required capability_ids
        self._dependency_graph: dict[str, set[str]] = {}

    def register_capability(self, capability: Capability, *, feature_ids: tuple[str, ...] = ()) -> None:
        normalized_capability = Capability(
            capability_id=capability.capability_id.strip(),
            name=capability.name.strip(),
            description=capability.description.strip(),
            category=capability.category.strip(),
            default_enabled=bool(capability.default_enabled),
            monetizable=bool(capability.monetizable),
            usage_metered=bool(capability.usage_metered),
            metadata={
                str(key).strip(): str(value).strip()
                for key, value in capability.metadata.items()
                if str(key).strip() and str(value).strip()
            },
            price=capability.price,
            usage_based=bool(capability.usage_metered),
            included_in_plans=tuple(sorted({plan.strip().lower() for plan in capability.included_in_plans if plan.strip()})),
            included_in_add_ons=tuple(sorted({addon.strip().lower() for addon in capability.included_in_add_ons if addon.strip()})),
            domain=capability.domain.strip(),
            required_adapters=tuple(a.strip() for a in capability.required_adapters if a.strip()),
        )
        if not normalized_capability.capability_id:
            raise ValueError("capability_id is required")
        # MS-CAP-01 + MS-CAP-02 validation gates (MS§2.2, MS§2.3)
        self._validate_ms_cap_01(normalized_capability)
        self._validate_ms_cap_02(normalized_capability)

        index = capability_index()
        index[normalized_capability.capability_id] = normalized_capability

        mapping = feature_capability_mapping()
        for feature_id in feature_ids:
            normalized_feature = feature_id.strip()
            if normalized_feature:
                mapping[normalized_feature] = normalized_capability.capability_id

    # ------------------------------------------------------------------ #
    # MS-CAP-01 — Capability Definition Completeness (MS§2.2)            #
    # MS-CAP-02 — Capability Validity Rule (MS§2.3)                      #
    # ------------------------------------------------------------------ #

    def _validate_ms_cap_01(self, capability: Capability) -> None:
        """MS-CAP-01: reject registration if any of the 6 required fields is absent.

        Required fields per MS§2.2:
          unique_key (capability_id), domain, dependencies*, usage_metrics,
          billing_type (derivable), required_adapters.

        * dependencies are registered separately via register_capability_dependencies();
          completeness of dependency declarations is enforced there.
        """
        from decimal import Decimal
        errors: list[str] = []

        # unique_key — capability_id already checked above; belt-and-braces
        if not capability.capability_id:
            errors.append("unique_key (capability_id) is required")

        # domain — must be a non-empty owner domain string
        if not capability.domain:
            errors.append("domain is required (e.g. 'commerce', 'learning', 'ai')")

        # usage_metrics — monetizable capability must have at least one measurement path
        has_price = capability.price is not None and capability.price > Decimal("0")
        if capability.monetizable and not capability.usage_metered and not has_price:
            errors.append(
                "usage_metrics required: monetizable capability must have "
                "usage_metered=True or price > 0"
            )

        # billing_type — must be determinable: non-monetizable, or belongs to a plan/add-on, or has a price
        if capability.monetizable:
            has_plan = len(capability.included_in_plans) > 0
            has_addon = len(capability.included_in_add_ons) > 0
            if not has_plan and not has_addon and not has_price:
                errors.append(
                    "billing_type undetermined: monetizable capability must appear in "
                    "included_in_plans, included_in_add_ons, or have price > 0"
                )

        # required_adapters — field must be present; empty tuple is valid (no external deps)
        # Field always present after model addition — no additional check needed here

        # BC-LANG-01 / MO-031: monetizable capabilities must carry a business_impact_description
        if capability.monetizable and not capability.business_impact_description.strip():
            errors.append(
                "business_impact_description is required for monetizable capabilities "
                "(BC-LANG-01): state the operator-facing business outcome, e.g. "
                "'Recover up to 30% of unpaid fees via automated WhatsApp reminders'"
            )

        if errors:
            raise ValueError(
                f"MS-CAP-01 completeness violation for '{capability.capability_id}': "
                + "; ".join(errors)
            )

    def _validate_ms_cap_02(self, capability: Capability) -> None:
        """MS-CAP-02: reject registration if any validity condition fails.

        Three conditions per MS§2.3:
          1. Independently enable/disable — no self-dependency (cycle check in dep registration)
          2. Independently measurable — at least one measurement path if monetizable
          3. Reusable — not marked tenant_specific in metadata
        """
        from decimal import Decimal
        errors: list[str] = []

        # Condition 1: independently enable/disable — self-dependency check
        # (circular dependency across capabilities caught in register_capability_dependencies)
        if capability.capability_id in self.get_dependencies(capability.capability_id):
            errors.append(
                "independently enable/disable violated: self-dependency detected"
            )

        # Condition 2: independently measurable
        has_price = capability.price is not None and capability.price > Decimal("0")
        if capability.monetizable and not capability.usage_metered and not has_price:
            errors.append(
                "independently measurable violated: monetizable capability must have "
                "usage_metered=True or price > 0"
            )

        # Condition 3: reusable — must not be flagged as tenant-specific
        if capability.metadata.get("tenant_specific", "").lower() in ("true", "1", "yes"):
            errors.append(
                "reusable violated: capability is marked tenant_specific=true in metadata; "
                "use config parameters for tenant-specific variants instead"
            )

        if errors:
            raise ValueError(
                f"MS-CAP-02 validity violation for '{capability.capability_id}': "
                + "; ".join(errors)
            )

    def get_capability(self, capability_id: str) -> Capability | None:
        return capability_index().get(capability_id.strip())

    def list_capabilities(self) -> list[Capability]:
        return sorted(capability_index().values(), key=lambda item: item.capability_id)

    def get_capability_for_feature(self, feature_id: str) -> Capability | None:
        mapped_capability_id = feature_capability_mapping().get(feature_id.strip())
        if not mapped_capability_id:
            return None
        return self.get_capability(mapped_capability_id)

    def get_capability_pricing(self, capability_id: str) -> CapabilityPricing | None:
        capability = self.get_capability(capability_id)
        return capability.pricing if capability else None


    def list_plan_capabilities(self, plan_type: str) -> set[str]:
        normalized_plan = plan_type.strip().lower()
        return {
            capability.capability_id
            for capability in self.list_capabilities()
            if normalized_plan in capability.included_in_plans
        }

    def list_add_on_capabilities(self, add_on: str) -> set[str]:
        normalized_add_on = add_on.strip().lower()
        return {
            capability.capability_id
            for capability in self.list_capabilities()
            if normalized_add_on in capability.included_in_add_ons
        }

    def assert_capability_is_single_billing_unit(self, capability_id: str) -> bool:
        """Validate that a monetizable capability maps to exactly one billing unit.

        B2P05 / capability_registry_service_spec: a billing unit is one of:
          - a plan tier (entry in included_in_plans)
          - an add-on (entry in included_in_add_ons)
          - a standalone price (monetizable=True with price > 0, no plan/add-on)

        Rules:
          - Non-monetizable capabilities always pass (not a billing concern).
          - Monetizable capabilities must belong to exactly one billing context:
            either exactly one plan tier, or one add-on, or a direct price only.
          - Being in BOTH a plan AND having a standalone price > 0 is a multi-unit
            violation and returns False.
          - Having no billing context at all (monetizable=True but no plan, no
            add-on, no price) also returns False — dangling billing unit.
        """
        from decimal import Decimal
        capability = self.get_capability(capability_id)
        if capability is None:
            return False
        if not capability.monetizable:
            return True  # non-monetized: single billing unit rule doesn't apply
        plan_count = len(capability.included_in_plans)
        addon_count = len(capability.included_in_add_ons)
        has_price = capability.price is not None and capability.price > Decimal("0")
        billing_unit_count = plan_count + addon_count + (1 if has_price else 0)
        # Exactly one billing context = single billing unit
        return billing_unit_count == 1

    def is_enabled_by_default(self, capability_id: str) -> bool:
        """Registry default signal consumed by entitlement service only."""
        capability = self.get_capability(capability_id)
        return bool(capability.default_enabled) if capability else False

    # ------------------------------------------------------------------ #
    # B2P05 — Dependency graph                                            #
    # ------------------------------------------------------------------ #

    def register_capability_dependencies(
        self,
        capability_id: str,
        depends_on: tuple[str, ...] | list[str],
    ) -> None:
        """Register dependency edges for a capability.

        B2P05: each capability may declare required service dependencies.
        Dependencies must be registered separately from the capability record —
        callers register the capability first, then declare its dependencies.
        """
        cap_id = capability_id.strip()
        if not cap_id:
            raise ValueError("capability_id is required")
        self._dependency_graph.setdefault(cap_id, set())
        for dep in depends_on:
            dep_id = dep.strip()
            if not dep_id:
                continue
            # MS-CAP-02 condition 1: self-dependency violates independent enable/disable
            if dep_id == cap_id:
                raise ValueError(
                    f"MS-CAP-02 validity violation: self-dependency detected for '{cap_id}'"
                )
            self._dependency_graph[cap_id].add(dep_id)

    def get_dependencies(self, capability_id: str) -> set[str]:
        """Return the set of capability_ids that this capability depends on."""
        return set(self._dependency_graph.get(capability_id.strip(), set()))

    # ------------------------------------------------------------------
    # BC-FREE-01: Free tier capability bundle — MO-027 / Phase C
    # Registers the quota-capped capability bundle that constitutes the
    # free tier. Free tier must deliver complete operational value:
    # payment collection, enrollment (50 students), basic WhatsApp
    # (100 messages/month), Daily Action List. Limits are by scope
    # depth — core functions are never disabled.
    # ------------------------------------------------------------------

    def register_free_tier_capability_bundle(self) -> list[str]:
        """Register all free-tier capabilities with BC-FREE-01 quota constraints.

        Returns list of registered capability_ids.
        Called at platform bootstrap — idempotent (re-registration is safe).
        """
        from decimal import Decimal

        FREE_TIER_CAPABILITIES: list[dict] = [
            {
                "capability_id": "CAP-ENROLL-FREE",
                "name": "Student Enrollment (Free)",
                "description": "Enroll and manage students up to the free tier limit.",
                "business_impact_description": "Manage up to 50 active students — enough to run a full class with no upfront cost.",
                "category": "enrollment",
                "domain": "learning",
                "default_enabled": True,
                "monetizable": True,
                "usage_metered": True,
                "usage_quota": 50,
                "included_in_plans": ("free",),
                "price": Decimal("0"),
            },
            {
                "capability_id": "CAP-PAYMENT-FREE",
                "name": "Payment Collection (Free)",
                "description": "Collect fee payments from students via supported payment methods.",
                "business_impact_description": "Accept fee payments from day one — payment collection is never locked behind a paid plan.",
                "category": "commerce",
                "domain": "commerce",
                "default_enabled": True,
                "monetizable": True,
                "usage_metered": False,
                "usage_quota": None,
                "included_in_plans": ("free",),
                "price": Decimal("0"),
            },
            {
                "capability_id": "CAP-WHATSAPP-FREE",
                "name": "WhatsApp Messaging (Free)",
                "description": "Send WhatsApp notifications and reminders up to the free tier monthly limit.",
                "business_impact_description": "Reach students and parents via WhatsApp — 100 messages/month included at no cost.",
                "category": "communication",
                "domain": "communication",
                "default_enabled": True,
                "monetizable": True,
                "usage_metered": True,
                "usage_quota": 100,
                "included_in_plans": ("free",),
                "price": Decimal("0"),
            },
            {
                "capability_id": "CAP-DAILY-ACTION-LIST-FREE",
                "name": "Daily Action List (Free)",
                "description": "Operator-facing daily list of unpaid fees, absentees, and urgent actions.",
                "business_impact_description": "Know exactly what needs attention today — unpaid fees, absent students, urgent tasks — without opening any dashboard.",
                "category": "operations",
                "domain": "operations",
                "default_enabled": True,
                "monetizable": True,
                "usage_metered": False,
                "usage_quota": None,
                "included_in_plans": ("free",),
                "price": Decimal("0"),
            },
        ]

        registered: list[str] = []
        for cap_def in FREE_TIER_CAPABILITIES:
            capability = Capability(
                capability_id=cap_def["capability_id"],
                name=cap_def["name"],
                description=cap_def["description"],
                business_impact_description=cap_def["business_impact_description"],
                category=cap_def["category"],
                domain=cap_def["domain"],
                default_enabled=cap_def["default_enabled"],
                monetizable=cap_def["monetizable"],
                usage_metered=cap_def["usage_metered"],
                usage_quota=cap_def.get("usage_quota"),
                included_in_plans=tuple(cap_def.get("included_in_plans", ())),
                price=cap_def["price"],
            )
            self.register_capability(capability)
            registered.append(capability.capability_id)

        return registered

    def get_dependents(self, capability_id: str) -> set[str]:
        """Return capability_ids that declare a dependency on this capability (reverse lookup)."""
        cap_id = capability_id.strip()
        return {
            cid for cid, deps in self._dependency_graph.items()
            if cap_id in deps
        }

    def validate_dependencies_met(self, capability_id: str) -> tuple[bool, list[str]]:
        """B2P05: validate all declared dependencies for a capability are registered.

        Returns (all_met, missing_ids). A capability should not be activated if
        any dependency is missing from the registry.
        """
        required = self.get_dependencies(capability_id)
        registered = {cap.capability_id for cap in self.list_capabilities()}
        missing = [dep for dep in sorted(required) if dep not in registered]
        return (len(missing) == 0, missing)
