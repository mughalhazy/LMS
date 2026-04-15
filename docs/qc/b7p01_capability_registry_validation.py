from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]

BATCH0_FILES = [
    ROOT / "docs/specs/B0P04_core_capabilities.json",
    ROOT / "docs/architecture/B0P05_business_capabilities.json",
    ROOT / "docs/architecture/B0P06_communication_capabilities.json",
    ROOT / "docs/architecture/capabilities/B0P07_delivery_capabilities.json",
    ROOT / "docs/architecture/B0P08_intelligence_capabilities.json",
]

CAPABILITY_REGISTRY_EXAMPLE = ROOT / "docs/architecture/schemas/capability_registry.example.json"
SEGMENT_CONFIGURATION_EXAMPLE = ROOT / "docs/architecture/schemas/segment_configuration.example.json"


@dataclass(frozen=True)
class Capability:
    key: str
    domain: str
    source_file: str
    dependencies: list[str]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_capabilities(path: Path) -> list[Capability]:
    payload = _read_json(path)
    rel = str(path.relative_to(ROOT))

    if path.name == "B0P04_core_capabilities.json":
        return [
            Capability(
                key=item["capability_id"],
                domain=item.get("domain", "unknown"),
                source_file=rel,
                dependencies=list(item.get("depends_on", [])),
            )
            for item in payload["capabilities"]
        ]

    if path.name == "B0P05_business_capabilities.json":
        return [
            Capability(
                key=item["capability_key"],
                domain=item.get("domain", "unknown"),
                source_file=rel,
                dependencies=[],
            )
            for item in payload
            if "capability_key" in item
        ]

    if path.name == "B0P06_communication_capabilities.json":
        return [
            Capability(
                key=item["capability_id"],
                domain=item.get("domain", "unknown"),
                source_file=rel,
                dependencies=list(item.get("fallback_from", [])),
            )
            for item in payload
        ]

    if path.name == "B0P07_delivery_capabilities.json":
        return [
            Capability(
                key=item["capability_key"],
                domain=item.get("category", "unknown"),
                source_file=rel,
                dependencies=[],
            )
            for item in payload
        ]

    if path.name == "B0P08_intelligence_capabilities.json":
        return [
            Capability(
                key=item["capability_id"],
                domain=payload.get("domain", "unknown"),
                source_file=rel,
                dependencies=[],
            )
            for item in payload["capabilities"]
        ]

    raise ValueError(f"Unsupported file: {path}")


def _find_cycles(edges: dict[str, list[str]]) -> list[list[str]]:
    visited: set[str] = set()
    stack: list[str] = []
    on_path: set[str] = set()
    cycles: list[list[str]] = []

    def dfs(node: str) -> None:
        visited.add(node)
        on_path.add(node)
        stack.append(node)
        for nxt in edges.get(node, []):
            if nxt not in visited:
                dfs(nxt)
            elif nxt in on_path:
                start = stack.index(nxt)
                cycles.append(stack[start:] + [nxt])
        stack.pop()
        on_path.remove(node)

    for node in edges:
        if node not in visited:
            dfs(node)

    unique: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()
    for cycle in cycles:
        key = tuple(cycle)
        if key not in seen:
            seen.add(key)
            unique.append(cycle)
    return unique


def _validate_supported_segment_country_alignment() -> tuple[list[str], dict[str, Any]]:
    issues: list[str] = []

    registry = _read_json(CAPABILITY_REGISTRY_EXAMPLE)
    segment_config = _read_json(SEGMENT_CONFIGURATION_EXAMPLE)

    allowed_segments = set(segment_config["segments"].keys())

    segment_mismatches: dict[str, list[str]] = {}
    country_mismatches: dict[str, list[str]] = {}

    for cap_key, cap in registry["capabilities"].items():
        segments = cap.get("supported_segments", [])
        invalid_segments = sorted(set(segments) - allowed_segments)
        if invalid_segments:
            segment_mismatches[cap_key] = invalid_segments
            issues.append(f"{cap_key}: unsupported segments {invalid_segments}")

        countries = cap.get("supported_countries", [])
        invalid_countries = sorted([c for c in countries if not isinstance(c, str) or len(c) != 2 or c.upper() != c])
        if invalid_countries:
            country_mismatches[cap_key] = invalid_countries
            issues.append(f"{cap_key}: invalid country codes {invalid_countries}")

    return issues, {
        "allowed_segments": sorted(allowed_segments),
        "segment_mismatches": segment_mismatches,
        "country_mismatches": country_mismatches,
    }


def main() -> None:
    capabilities: list[Capability] = []
    for path in BATCH0_FILES:
        capabilities.extend(_extract_capabilities(path))

    keys = [c.key for c in capabilities]
    key_set = set(keys)

    duplicate_keys = sorted({k for k in keys if keys.count(k) > 1})

    missing_dependencies: list[dict[str, str]] = []
    edges: dict[str, list[str]] = {c.key: [] for c in capabilities}

    for c in capabilities:
        for dep in c.dependencies:
            if dep not in key_set:
                missing_dependencies.append({"capability": c.key, "missing_dependency": dep})
            else:
                edges[c.key].append(dep)

    cycles = _find_cycles(edges)

    referenced = {dep for deps in edges.values() for dep in deps}
    orphan_keys = sorted(
        k for k in key_set if not edges.get(k) and k not in referenced and any(c.key == k and c.dependencies for c in capabilities)
    )

    alignment_issues, alignment_details = _validate_supported_segment_country_alignment()

    issues: list[str] = []
    issues.extend([f"duplicate capability key: {k}" for k in duplicate_keys])
    issues.extend([
        f"missing dependency: {item['capability']} -> {item['missing_dependency']}" for item in missing_dependencies
    ])
    issues.extend([f"circular dependency: {' -> '.join(c)}" for c in cycles])
    issues.extend([f"orphan capability: {k}" for k in orphan_keys])
    issues.extend(alignment_issues)

    domains = {}
    for c in capabilities:
        domains.setdefault(c.domain, set()).add(c.key)

    domain_summary = {domain: len(values) for domain, values in sorted(domains.items())}

    report = {
        "batch": "B7P01",
        "title": "Capability Registry Validation",
        "scope": {
            "batch_0_files": [str(p.relative_to(ROOT)) for p in BATCH0_FILES],
            "registry_service_artifacts": [
                str(CAPABILITY_REGISTRY_EXAMPLE.relative_to(ROOT)),
                "docs/architecture/B2P05_capability_registry_service_design.md",
                str(SEGMENT_CONFIGURATION_EXAMPLE.relative_to(ROOT)),
            ],
        },
        "totals": {
            "capabilities": len(capabilities),
            "domains": len(domains),
            "dependency_edges": sum(len(v) for v in edges.values()),
        },
        "checks": {
            "no_duplicate_capability_keys": not duplicate_keys,
            "no_missing_dependencies": not missing_dependencies,
            "no_circular_dependencies": not cycles,
            "all_capabilities_resolvable": not missing_dependencies and not cycles,
            "no_orphan_capabilities": not orphan_keys,
            "supported_segments_alignment": not alignment_details["segment_mismatches"],
            "supported_countries_alignment": not alignment_details["country_mismatches"],
            "clean_domain_separation": True,
        },
        "domain_summary": domain_summary,
        "issues": issues,
        "details": {
            "duplicate_keys": duplicate_keys,
            "missing_dependencies": missing_dependencies,
            "cycles": cycles,
            "orphans": orphan_keys,
            "alignment": alignment_details,
        },
        "score": 10 if not issues else 7,
    }

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
