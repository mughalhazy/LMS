from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from .models import CapabilityDecision, EntitlementContext, EntitlementResult
from .store import InMemoryPolicyStore, InMemoryRegistryReader


class EntitlementService:
    def __init__(self, policy_store: InMemoryPolicyStore, registry: InMemoryRegistryReader) -> None:
        self.policy_store = policy_store
        self.registry = registry

    def resolve(self, ctx: EntitlementContext) -> Tuple[int, Dict[str, Any]]:
        result = self._evaluate(ctx)
        # B09-001: entitlement-interface-contract.md — each capability must include
        # dependencies.required + dependencies.missing per CapabilityEntitlement contract
        decisions_out = {}
        for k, d in result.decisions.items():
            required_deps = self.registry.get_dependencies(k)
            missing_deps = [
                dep for dep in required_deps
                if not result.decisions.get(dep, CapabilityDecision(key=dep, enabled=False)).enabled
            ]
            decisions_out[k] = {
                "state": "enabled" if d.enabled else "disabled",
                "enabled": d.enabled,
                "reasons": d.reasons,
                "dependencies": {"required": required_deps, "missing": missing_deps},
            }
        return 200, {
            "decisions": decisions_out,
            "normalized_context": result.normalized_context,
            "policy_revisions": [result.policy_revision] if result.policy_revision else [],
            "registry_version": result.registry_version,
            "resolved_at": result.resolved_at.isoformat(),
            "evaluation_order": result.evaluation_order,
        }

    def is_enabled(self, ctx: EntitlementContext, capability_key: str) -> Tuple[int, Dict[str, Any]]:
        result = self._evaluate(ctx)
        decision = result.decisions.get(capability_key)
        if decision is None:
            return 200, {"capability_key": capability_key, "enabled": False, "reasons": ["not_in_registry"]}
        return 200, {
            "capability_key": capability_key,
            "enabled": decision.enabled,
            "reasons": decision.reasons,
        }

    def _evaluate(self, ctx: EntitlementContext) -> EntitlementResult:
        # Step 1: normalize — sort and deduplicate add-ons lexicographically
        normalized_addons = sorted(set(ctx.add_ons))
        evaluation_order: List[str] = []

        candidate: Dict[str, CapabilityDecision] = {}

        # Step 2: base policy grants/denials
        base_policies = self.policy_store.get_base_policies(ctx.segment, ctx.plan, ctx.country)
        evaluation_order.append("base_plan")
        for p in base_policies:
            if p.capability_key not in candidate:
                candidate[p.capability_key] = CapabilityDecision(key=p.capability_key, enabled=False)
            dec = candidate[p.capability_key]
            if p.granted:
                dec.enabled = True
                dec.reasons.append("base_plan")
            else:
                # deny wins over grant
                dec.enabled = False
                if "denied_by_policy" not in dec.reasons:
                    dec.reasons.append("denied_by_policy")

        # Step 3: add-on policy grants/denials in sorted lexical order
        for add_on in normalized_addons:
            addon_policies = self.policy_store.get_addon_policies(add_on, ctx.segment, ctx.plan, ctx.country)
            evaluation_order.append(f"addon:{add_on}")
            for p in addon_policies:
                if p.capability_key not in candidate:
                    candidate[p.capability_key] = CapabilityDecision(key=p.capability_key, enabled=False)
                dec = candidate[p.capability_key]
                if p.granted:
                    # only grant if not already denied
                    if "denied_by_policy" not in dec.reasons:
                        dec.enabled = True
                        source = f"addon:{add_on}"
                        if source not in dec.reasons:
                            dec.reasons.append(source)
                else:
                    dec.enabled = False
                    if "denied_by_policy" not in dec.reasons:
                        dec.reasons.append("denied_by_policy")

        # Step 4: dependency enforcement via registry
        for key in list(candidate.keys()):
            dec = candidate[key]
            if not dec.enabled:
                continue
            deps = self.registry.get_dependencies(key)
            missing = [d for d in deps if not candidate.get(d, CapabilityDecision(key=d, enabled=False)).enabled]
            if missing:
                dec.enabled = False
                for m in missing:
                    dec.reasons.append(f"missing_dependency:{m}")

        normalized_context = {
            "tenant_id": ctx.tenant_id,
            "segment": ctx.segment,
            "plan": ctx.plan,
            "country": ctx.country,
            "add_ons": normalized_addons,
        }

        return EntitlementResult(
            decisions=candidate,
            normalized_context=normalized_context,
            policy_revision=self.policy_store.revision,
            registry_version=self.registry.version,
            resolved_at=datetime.now(timezone.utc),
            evaluation_order=evaluation_order,
        )
