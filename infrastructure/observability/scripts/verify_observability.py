from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = ROOT / "backend" / "services"
OBS_DIR = ROOT / "infrastructure" / "observability"


def _load_targets(path: Path) -> dict[str, dict]:
    content = json.loads(path.read_text())
    output: dict[str, dict] = {}
    for item in content:
        service = item.get("labels", {}).get("service")
        if service:
            output[service] = item
    return output


def _service_names() -> list[str]:
    return sorted([p.name for p in SERVICES_DIR.iterdir() if p.is_dir()])


def verify_metrics_targets() -> tuple[bool, list[str]]:
    service_names = _service_names()
    metrics_targets = _load_targets(OBS_DIR / "services" / "services-targets.json")

    missing_services = [name for name in service_names if name not in metrics_targets]
    invalid_targets = [
        name
        for name, target in metrics_targets.items()
        if target.get("labels", {}).get("metrics_path") != "/metrics"
        or not target.get("targets")
    ]

    issues: list[str] = []
    if missing_services:
        issues.append(f"Missing metrics target for services: {', '.join(missing_services)}")
    if invalid_targets:
        issues.append(
            "Metrics targets are missing /metrics configuration or targets: "
            f"{', '.join(sorted(invalid_targets))}"
        )

    return not issues, issues


def verify_health_targets() -> tuple[bool, list[str]]:
    service_names = _service_names()
    health_targets = _load_targets(OBS_DIR / "services" / "services-health-targets.json")

    missing_services = [name for name in service_names if name not in health_targets]
    invalid_targets = [
        name
        for name, target in health_targets.items()
        if not any(str(endpoint).endswith("/health") for endpoint in target.get("targets", []))
    ]

    issues: list[str] = []
    if missing_services:
        issues.append(f"Missing health target for services: {', '.join(missing_services)}")
    if invalid_targets:
        issues.append(
            "Health targets not pointing to /health endpoint: "
            f"{', '.join(sorted(invalid_targets))}"
        )

    return not issues, issues


def verify_service_endpoints_declared() -> tuple[bool, list[str]]:
    issues: list[str] = []
    for service_dir in sorted(p for p in SERVICES_DIR.iterdir() if p.is_dir()):
        main_py = service_dir / "app" / "main.py"
        index_js = service_dir / "src" / "index.js"

        if main_py.exists():
            content = main_py.read_text()
            has_health = '"/health"' in content or "'/health'" in content
            has_metrics = '"/metrics"' in content or "'/metrics'" in content
            if not has_health or not has_metrics:
                missing = []
                if not has_health:
                    missing.append("/health")
                if not has_metrics:
                    missing.append("/metrics")
                issues.append(f"{service_dir.name} missing endpoints: {', '.join(missing)}")
        elif index_js.exists():
            content = index_js.read_text()
            has_health = "health" in content.lower()
            has_metrics = "/metrics" in content or "metrics" in content.lower()
            if not has_health or not has_metrics:
                missing = []
                if not has_health:
                    missing.append("/health")
                if not has_metrics:
                    missing.append("/metrics")
                issues.append(f"{service_dir.name} missing endpoints: {', '.join(missing)}")

    return not issues, issues


def verify_central_logging_and_tracing() -> tuple[bool, bool, list[str]]:
    otel_cfg = (OBS_DIR / "config" / "otel" / "otel-collector.yml").read_text()
    promtail_cfg = (OBS_DIR / "config" / "promtail" / "promtail.yml").read_text()

    logging_ok = all(
        snippet in otel_cfg
        for snippet in ["exporters:", "loki:", "pipelines:", "logs:", "exporters: [loki]"]
    ) and all(snippet in promtail_cfg for snippet in ["clients:", "http://loki:3100/loki/api/v1/push"])

    tracing_ok = all(
        snippet in otel_cfg
        for snippet in ["otlp/tempo:", "traces:", "exporters: [otlp/tempo]"]
    )

    issues: list[str] = []
    if not logging_ok:
        issues.append("Centralized logging is not fully configured across OTEL collector and Promtail")
    if not tracing_ok:
        issues.append("Distributed tracing is not fully configured in OTEL collector")

    return logging_ok, tracing_ok, issues


def verify_dashboards_configured() -> tuple[bool, list[str]]:
    dashboard_provisioning = (
        OBS_DIR / "config" / "grafana" / "provisioning" / "dashboards" / "dashboards.yml"
    ).read_text()
    datasources = (
        OBS_DIR / "config" / "grafana" / "provisioning" / "datasources" / "datasources.yml"
    ).read_text()
    dashboard_json = OBS_DIR / "dashboards" / "service-observability-overview.json"

    dashboard_ok = (
        "providers:" in dashboard_provisioning
        and "path: /var/lib/grafana/dashboards" in dashboard_provisioning
        and all(name in datasources for name in ["Prometheus", "Loki", "Tempo"])
        and dashboard_json.exists()
    )

    issues: list[str] = []
    if not dashboard_ok:
        issues.append("Grafana dashboards/datasources are not fully provisioned")

    return dashboard_ok, issues


def main() -> None:
    metrics_ok, metrics_issues = verify_metrics_targets()
    health_ok, health_issues = verify_health_targets()
    endpoints_ok, endpoint_issues = verify_service_endpoints_declared()
    logging_ok, tracing_ok, telemetry_issues = verify_central_logging_and_tracing()
    dashboards_ok, dashboard_issues = verify_dashboards_configured()

    checks = {
        "centralized_logging_enabled": logging_ok,
        "metrics_exported_from_services": metrics_ok,
        "distributed_tracing_enabled": tracing_ok,
        "health_endpoints_implemented": health_ok and endpoints_ok,
        "monitoring_dashboards_configured": dashboards_ok,
    }

    passed = sum(1 for value in checks.values() if value)
    monitoring_score = passed * 2

    issues = metrics_issues + health_issues + endpoint_issues + telemetry_issues + dashboard_issues
    if issues:
        print("observability_issues")
        for issue in issues:
            print(f"- {issue}")

    print(f"services_monitored={len(_service_names())}")
    print(f"metrics_verified={'yes' if metrics_ok and endpoints_ok else 'no'}")
    print(f"observability_score={monitoring_score}/10")

    assert monitoring_score == 10, "Observability validation failed; score is below 10/10"


if __name__ == "__main__":
    main()
