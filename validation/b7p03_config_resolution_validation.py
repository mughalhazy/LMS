from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

CONFIG_SERVICE_DESIGN = ROOT / "docs/architecture/B2P01_config_service_design.md"
CONFIG_RESOLUTION_CONTRACT = ROOT / "docs/architecture/config_resolution_interface_contract.md"
SEGMENT_CONFIGURATION_EXAMPLE = ROOT / "docs/architecture/schemas/segment_configuration.example.json"


@dataclass(frozen=True)
class ResolutionContext:
    tenant_id: str
    country: str
    segment: str
    plan: str


@dataclass(frozen=True)
class Scenario:
    name: str
    context: ResolutionContext
    overrides: dict[str, Any]


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_global_layer() -> dict[str, Any]:
    return {
        "feature.chat.enabled": False,
        "ui.locale.default": "en-US",
        "limits.max_concurrent_sessions": 100,
        "reporting.retention_days": 30,
        "security.mfa.required": False,
    }


def _build_country_layers() -> dict[str, dict[str, Any]]:
    """Batch 4 country config fixture used for QC-only validation."""

    return {
        "US": {
            "ui.locale.default": "en-US",
            "reporting.retention_days": 45,
            "security.mfa.required": True,
        },
        "GB": {
            "ui.locale.default": "en-GB",
            "reporting.retention_days": 60,
        },
        "AE": {
            "ui.locale.default": "ar-AE",
            "reporting.retention_days": 90,
            "limits.max_concurrent_sessions": 140,
        },
    }


def _build_plan_layers() -> dict[str, dict[str, Any]]:
    return {
        "starter": {
            "limits.max_concurrent_sessions": 180,
            "feature.chat.enabled": False,
        },
        "pro": {
            "limits.max_concurrent_sessions": 420,
            "feature.chat.enabled": True,
        },
        "enterprise": {
            "limits.max_concurrent_sessions": 1200,
            "feature.chat.enabled": True,
            "security.mfa.required": True,
        },
    }


def _build_tenant_layers() -> dict[str, dict[str, Any]]:
    return {
        "tenant_academy_us_01": {
            "limits.max_concurrent_sessions": 650,
            "tenant.branding.theme": "academy-dark",
        },
        "tenant_corporate_gb_77": {
            "feature.chat.enabled": False,
            "tenant.branding.theme": "corp-standard",
        },
        "tenant_multi_ae_99": {
            "tenant.branding.theme": "global-gold",
            "reporting.retention_days": 120,
        },
    }


def _build_segment_layer(segment_name: str, segment_config: dict[str, Any]) -> dict[str, Any]:
    segment = segment_config["segments"][segment_name]
    return {
        "segment.analytics_level": segment["behavior_flags"]["analytics_level"],
        "segment.compliance_level": segment["behavior_flags"]["compliance_level"],
        "limits.max_concurrent_sessions": segment["limits"]["max_concurrent_sessions"],
    }


def _resolve_config(
    scenario: Scenario,
    segment_config: dict[str, Any],
    global_layer: dict[str, Any],
    country_layers: dict[str, dict[str, Any]],
    plan_layers: dict[str, dict[str, Any]],
    tenant_layers: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    level_order = ["global", "country", "segment", "plan", "tenant", "override"]

    layers: dict[str, dict[str, Any]] = {
        "global": global_layer,
        "country": country_layers.get(scenario.context.country, {}),
        "segment": _build_segment_layer(scenario.context.segment, segment_config),
        "plan": plan_layers.get(scenario.context.plan, {}),
        "tenant": tenant_layers.get(scenario.context.tenant_id, {}),
        "override": scenario.overrides,
    }

    effective: dict[str, Any] = {}
    provenance: dict[str, str] = {}
    conflict_trace: dict[str, list[str]] = {}
    applied_levels: list[str] = []

    for level in level_order:
        payload = layers[level]
        if not payload:
            continue
        applied_levels.append(level)
        for key in sorted(payload.keys()):
            if key in effective:
                conflict_trace.setdefault(key, []).append(f"{provenance[key]}->{level}")
            effective[key] = payload[key]
            provenance[key] = level

    digest = hashlib.sha256(
        json.dumps(
            {
                "effective": effective,
                "provenance": provenance,
                "applied_levels": applied_levels,
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()

    return {
        "scenario": scenario.name,
        "context": {
            "tenant_id": scenario.context.tenant_id,
            "country": scenario.context.country,
            "segment": scenario.context.segment,
            "plan": scenario.context.plan,
        },
        "applied_levels": applied_levels,
        "effective": effective,
        "provenance": provenance,
        "conflict_trace": conflict_trace,
        "result_hash": digest,
    }


def _validate_order(applied_levels: list[str]) -> bool:
    expected_prefix = ["global", "country", "segment", "plan", "tenant", "override"]
    filtered_expected = [lvl for lvl in expected_prefix if lvl in applied_levels]
    return applied_levels == filtered_expected


def _detect_override_conflicts(result: dict[str, Any]) -> list[str]:
    issues: list[str] = []
    for key, transitions in sorted(result["conflict_trace"].items()):
        if len(transitions) != len(set(transitions)):
            issues.append(f"duplicate transition for key {key}: {transitions}")
    return issues


def _detect_layer_duplication(result: dict[str, Any]) -> list[str]:
    levels = result["applied_levels"]
    duplicates = sorted({lvl for lvl in levels if levels.count(lvl) > 1})
    return [f"duplicate layer application detected: {lvl}" for lvl in duplicates]


def main() -> None:
    segment_config = _read_json(SEGMENT_CONFIGURATION_EXAMPLE)
    global_layer = _build_global_layer()
    country_layers = _build_country_layers()
    plan_layers = _build_plan_layers()
    tenant_layers = _build_tenant_layers()

    scenarios = [
        Scenario(
            name="academy_us_pro_tenant_override",
            context=ResolutionContext(
                tenant_id="tenant_academy_us_01",
                country="US",
                segment="academy",
                plan="pro",
            ),
            overrides={"limits.max_concurrent_sessions": 700},
        ),
        Scenario(
            name="corporate_gb_starter_plan_wins_over_segment",
            context=ResolutionContext(
                tenant_id="tenant_corporate_gb_77",
                country="GB",
                segment="corporate",
                plan="starter",
            ),
            overrides={},
        ),
        Scenario(
            name="multinational_ae_enterprise_tenant_wins",
            context=ResolutionContext(
                tenant_id="tenant_multi_ae_99",
                country="AE",
                segment="multinational",
                plan="enterprise",
            ),
            overrides={"security.mfa.required": True},
        ),
    ]

    resolution_flow = [
        "normalize_context(tenant, country, segment, plan)",
        "fetch_layers(global -> country -> segment -> plan -> tenant)",
        "merge_layers_with_last_writer_wins",
        "apply_override_layer_if_present",
        "emit_effective_map_with_provenance_and_hash",
    ]

    results = [
        _resolve_config(s, segment_config, global_layer, country_layers, plan_layers, tenant_layers)
        for s in scenarios
    ]
    repeat_results = [
        _resolve_config(s, segment_config, global_layer, country_layers, plan_layers, tenant_layers)
        for s in scenarios
    ]

    hierarchy_issues: list[str] = []
    override_conflict_issues: list[str] = []
    duplication_issues: list[str] = []

    for result in results:
        if not _validate_order(result["applied_levels"]):
            hierarchy_issues.append(
                f"{result['scenario']}: invalid applied level order {result['applied_levels']}"
            )
        override_conflict_issues.extend(
            [f"{result['scenario']}: {issue}" for issue in _detect_override_conflicts(result)]
        )
        duplication_issues.extend(
            [f"{result['scenario']}: {issue}" for issue in _detect_layer_duplication(result)]
        )

    deterministic = all(
        first["result_hash"] == second["result_hash"]
        for first, second in zip(results, repeat_results, strict=True)
    )

    expected_values = {
        "academy_us_pro_tenant_override": {
            "limits.max_concurrent_sessions": (700, "override"),
            "feature.chat.enabled": (True, "plan"),
            "ui.locale.default": ("en-US", "country"),
        },
        "corporate_gb_starter_plan_wins_over_segment": {
            "limits.max_concurrent_sessions": (180, "plan"),
            "feature.chat.enabled": (False, "tenant"),
            "ui.locale.default": ("en-GB", "country"),
        },
        "multinational_ae_enterprise_tenant_wins": {
            "limits.max_concurrent_sessions": (1200, "plan"),
            "reporting.retention_days": (120, "tenant"),
            "security.mfa.required": (True, "override"),
        },
    }

    incorrect_override_behavior: list[str] = []
    for result in results:
        scenario_name = result["scenario"]
        for key, (expected_value, expected_source) in expected_values[scenario_name].items():
            actual_value = result["effective"].get(key)
            actual_source = result["provenance"].get(key)
            if actual_value != expected_value or actual_source != expected_source:
                incorrect_override_behavior.append(
                    f"{scenario_name}: key={key} expected=({expected_value},{expected_source}) "
                    f"actual=({actual_value},{actual_source})"
                )

    issues = [
        *hierarchy_issues,
        *override_conflict_issues,
        *duplication_issues,
        *incorrect_override_behavior,
    ]

    report = {
        "batch": "B7P03",
        "title": "Config Resolution Validation",
        "scope": {
            "config_service_batch_2": [
                str(CONFIG_SERVICE_DESIGN.relative_to(ROOT)),
                str(CONFIG_RESOLUTION_CONTRACT.relative_to(ROOT)),
            ],
            "country_config_batch_4": "qc_fixture_in_script:_build_country_layers",
            "segment_config_batch_0": [str(SEGMENT_CONFIGURATION_EXAMPLE.relative_to(ROOT))],
        },
        "resolution_flow": resolution_flow,
        "validation_report": {
            "scenario_count": len(scenarios),
            "segments_covered": sorted({s.context.segment for s in scenarios}),
            "countries_covered": sorted({s.context.country for s in scenarios}),
            "checks": {
                "no_hierarchy_violations": not hierarchy_issues,
                "no_override_conflicts": not override_conflict_issues,
                "deterministic_resolution": deterministic,
                "no_duplication_of_config_layers": not duplication_issues,
                "clear_priority_order": not hierarchy_issues,
                "overrides_work_correctly": not incorrect_override_behavior,
            },
            "issues": issues,
            "score": 10 if not issues and deterministic else 7,
        },
        "scenario_results": results,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
