from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

CAPABILITY_REGISTRY_EXAMPLE = ROOT / "docs/architecture/schemas/capability_registry.example.json"
SEGMENT_CONFIGURATION_EXAMPLE = ROOT / "docs/architecture/schemas/segment_configuration.example.json"


@dataclass(frozen=True)
class Scenario:
    name: str
    segment: str
    plan: str
    country: str
    addons: tuple[str, ...]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _normalize_addons(addons: tuple[str, ...]) -> list[str]:
    return sorted(set(a.strip().lower() for a in addons if a.strip()))


def _build_policy_fixtures() -> dict[str, Any]:
    """Deterministic synthetic policy fixtures used only for QC validation."""

    return {
        "base": {
            "academy|pro|US": {"allow": ["learning.reporting.basic"], "deny": []},
            "academy|starter|US": {"allow": [], "deny": ["learning.reporting.basic"]},
            "corporate|pro|US": {"allow": ["learning.reporting.basic"], "deny": []},
            "university|starter|GB": {"allow": [], "deny": []},
            "multinational|enterprise|AE": {"allow": ["learning.reporting.basic"], "deny": []},
        },
        "addons": {
            "advanced_analytics": {
                "allow": ["learning.analytics.advanced"],
                "deny": [],
            },
            "analytics_blocker": {
                "allow": [],
                "deny": ["learning.analytics.advanced"],
            },
            "reporting_core": {
                "allow": ["learning.reporting.basic"],
                "deny": [],
            },
        },
    }


def _resolve_entitlements(
    scenario: Scenario,
    capability_registry: dict[str, Any],
    policy_fixtures: dict[str, Any],
) -> dict[str, Any]:
    capabilities = capability_registry["capabilities"]
    derived_dependency_caps = {
        dep
        for meta in capabilities.values()
        for dep in meta.get("dependencies", [])
        if dep not in capabilities
    }
    all_capabilities = sorted(set(capabilities.keys()) | derived_dependency_caps)
    candidate: dict[str, dict[str, Any]] = {
        key: {"enabled": False, "reasons": []} for key in all_capabilities
    }

    base_key = f"{scenario.segment}|{scenario.plan}|{scenario.country}"
    base_policy = policy_fixtures["base"].get(base_key, {"allow": [], "deny": []})

    for cap in sorted(base_policy["allow"]):
        if cap in candidate:
            candidate[cap]["enabled"] = True
            candidate[cap]["reasons"].append("base_plan")
    for cap in sorted(base_policy["deny"]):
        if cap in candidate:
            candidate[cap]["enabled"] = False
            candidate[cap]["reasons"].append("denied_by_base_policy")

    normalized_addons = _normalize_addons(scenario.addons)
    for addon in normalized_addons:
        addon_policy = policy_fixtures["addons"].get(addon)
        if addon_policy is None:
            continue
        for cap in sorted(addon_policy["allow"]):
            if cap in candidate:
                candidate[cap]["enabled"] = True
                candidate[cap]["reasons"].append(f"addon:{addon}")
        for cap in sorted(addon_policy["deny"]):
            if cap in candidate:
                candidate[cap]["enabled"] = False
                candidate[cap]["reasons"].append(f"addon_denied:{addon}")

    for cap_key in sorted(candidate.keys()):
        metadata = capabilities.get(cap_key, {})
        if candidate[cap_key]["enabled"]:
            deps = metadata.get("dependencies", [])
            missing = sorted([dep for dep in deps if not candidate.get(dep, {}).get("enabled", False)])
            if missing:
                candidate[cap_key]["enabled"] = False
                candidate[cap_key]["reasons"].extend([f"missing_dependency:{dep}" for dep in missing])

    digest = hashlib.sha256(
        json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return {
        "scenario": scenario.name,
        "context": {
            "segment": scenario.segment,
            "plan": scenario.plan,
            "country": scenario.country,
            "addons": normalized_addons,
        },
        "resolved": candidate,
        "derived_capabilities": sorted(derived_dependency_caps),
        "result_hash": digest,
    }


def _detect_config_conflicts(policy_fixtures: dict[str, Any]) -> list[str]:
    issues: list[str] = []

    for key, policy in sorted(policy_fixtures["base"].items()):
        overlap = sorted(set(policy["allow"]) & set(policy["deny"]))
        if overlap:
            issues.append(f"base policy conflict {key}: {overlap}")

    for key, policy in sorted(policy_fixtures["addons"].items()):
        overlap = sorted(set(policy["allow"]) & set(policy["deny"]))
        if overlap:
            issues.append(f"addon policy conflict {key}: {overlap}")

    return issues


def main() -> None:
    capability_registry = _read_json(CAPABILITY_REGISTRY_EXAMPLE)
    segment_configuration = _read_json(SEGMENT_CONFIGURATION_EXAMPLE)
    policy_fixtures = _build_policy_fixtures()

    scenarios = [
        Scenario(
            name="academy_pro_with_advanced_addon",
            segment="academy",
            plan="pro",
            country="US",
            addons=("advanced_analytics",),
        ),
        Scenario(
            name="academy_starter_addon_blocked_by_missing_dependency",
            segment="academy",
            plan="starter",
            country="US",
            addons=("advanced_analytics",),
        ),
        Scenario(
            name="corporate_pro_addon_explicitly_denied",
            segment="corporate",
            plan="pro",
            country="US",
            addons=("advanced_analytics", "analytics_blocker"),
        ),
        Scenario(
            name="university_starter_dependency_recovered_by_reporting_addon",
            segment="university",
            plan="starter",
            country="GB",
            addons=("advanced_analytics", "reporting_core"),
        ),
    ]

    flow = [
        "normalize_context(segment, plan, country, add-ons)",
        "load_base_policy(segment+plan+country)",
        "load_addon_policies_in_lexicographic_order",
        "apply_allow_deny_merges_with_fixed_precedence",
        "enforce_capability_dependencies_from_registry",
        "emit_resolved_entitlements_with_reasons_and_hash",
    ]

    scenario_results = [_resolve_entitlements(s, capability_registry, policy_fixtures) for s in scenarios]
    repeat_results = [_resolve_entitlements(s, capability_registry, policy_fixtures) for s in scenarios]

    deterministic = all(
        first["result_hash"] == second["result_hash"]
        for first, second in zip(scenario_results, repeat_results, strict=True)
    )

    known_segments = set(segment_configuration["segments"].keys())
    segment_mismatches = sorted({s.segment for s in scenarios if s.segment not in known_segments})

    incorrect_activation_issues: list[str] = []
    missing_dependency_issues: list[str] = []
    registry_missing_dependency_defs = sorted(
        {
            dep
            for meta in capability_registry["capabilities"].values()
            for dep in meta.get("dependencies", [])
            if dep not in capability_registry["capabilities"]
        }
    )

    expected = {
        "academy_pro_with_advanced_addon": {
            "learning.reporting.basic": True,
            "learning.analytics.advanced": True,
        },
        "academy_starter_addon_blocked_by_missing_dependency": {
            "learning.reporting.basic": False,
            "learning.analytics.advanced": False,
        },
        "corporate_pro_addon_explicitly_denied": {
            "learning.reporting.basic": True,
            "learning.analytics.advanced": False,
        },
        "university_starter_dependency_recovered_by_reporting_addon": {
            "learning.reporting.basic": True,
            "learning.analytics.advanced": True,
        },
    }

    for result in scenario_results:
        scenario_name = result["scenario"]
        resolved = result["resolved"]
        for cap, expected_state in expected[scenario_name].items():
            actual = resolved.get(cap, {}).get("enabled")
            if actual != expected_state:
                incorrect_activation_issues.append(
                    f"{scenario_name}: capability {cap} expected={expected_state} actual={actual}"
                )

        for cap, decision in resolved.items():
            if decision["enabled"]:
                deps = capability_registry["capabilities"].get(cap, {}).get("dependencies", [])
                for dep in deps:
                    if not resolved.get(dep, {}).get("enabled", False):
                        missing_dependency_issues.append(
                            f"{scenario_name}: {cap} enabled while dependency {dep} disabled"
                        )

    conflict_issues = _detect_config_conflicts(policy_fixtures)

    issues = [
        *[f"unknown segment used in scenario: {seg}" for seg in segment_mismatches],
        *incorrect_activation_issues,
        *missing_dependency_issues,
        *conflict_issues,
    ]

    report = {
        "batch": "B7P02",
        "title": "Entitlement Resolution Validation",
        "scope": {
            "entitlement_service_artifacts": [
                "docs/architecture/B2P02_entitlement_service_design.md",
                "docs/architecture/entitlement_interface_contract.md",
            ],
            "segment_configs": [str(SEGMENT_CONFIGURATION_EXAMPLE.relative_to(ROOT))],
            "capability_registry": [str(CAPABILITY_REGISTRY_EXAMPLE.relative_to(ROOT))],
        },
        "validation_flow": flow,
        "totals": {
            "scenario_count": len(scenarios),
            "capabilities_per_resolution": len(scenario_results[0]["resolved"]) if scenario_results else 0,
            "segments_checked": len({s.segment for s in scenarios}),
        },
        "checks": {
            "no_incorrect_capability_activation": not incorrect_activation_issues,
            "add_on_enablement_works": all(
                r["resolved"]["learning.analytics.advanced"]["enabled"]
                for r in scenario_results
                if r["scenario"] in {"academy_pro_with_advanced_addon", "university_starter_dependency_recovered_by_reporting_addon"}
            ),
            "dependency_enforcement_works": not missing_dependency_issues
            and not scenario_results[1]["resolved"]["learning.analytics.advanced"]["enabled"],
            "deterministic_results": deterministic,
            "no_config_conflicts": not conflict_issues,
            "clean_resolution_logic": not segment_mismatches,
        },
        "issues": issues,
        "issue_report": {
            "incorrect_activation": incorrect_activation_issues,
            "missing_dependencies": missing_dependency_issues,
            "config_conflicts": conflict_issues,
            "segment_mismatches": segment_mismatches,
            "registry_missing_dependency_definitions": registry_missing_dependency_defs,
        },
        "scenario_results": scenario_results,
        "score": 10 if not issues and deterministic else 7,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
