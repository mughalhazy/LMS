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


def verify_metrics_targets() -> None:
    service_names = sorted([p.name for p in SERVICES_DIR.iterdir() if p.is_dir()])
    metrics_targets = _load_targets(OBS_DIR / "services" / "services-targets.json")
    missing = [name for name in service_names if name not in metrics_targets]
    assert not missing, f"Missing metrics target for services: {', '.join(missing)}"


def verify_health_targets() -> None:
    service_names = sorted([p.name for p in SERVICES_DIR.iterdir() if p.is_dir()])
    health_targets = _load_targets(OBS_DIR / "services" / "services-health-targets.json")
    missing = [name for name in service_names if name not in health_targets]
    assert not missing, f"Missing health target for services: {', '.join(missing)}"


def verify_central_logging_and_tracing() -> None:
    otel_cfg = (OBS_DIR / "config" / "otel" / "otel-collector.yml").read_text()
    promtail_cfg = (OBS_DIR / "config" / "promtail" / "promtail.yml").read_text()

    assert "exporters:" in otel_cfg and "loki:" in otel_cfg, "Loki exporter missing from OTEL config"
    assert "otlp/tempo:" in otel_cfg, "Tempo exporter missing from OTEL config"
    assert "clients:" in promtail_cfg and "loki" in promtail_cfg, "Promtail not configured to push to Loki"


def main() -> None:
    verify_metrics_targets()
    verify_health_targets()
    verify_central_logging_and_tracing()
    print("metrics_collected")
    print("logging_configured")
    print("tracing_enabled")


if __name__ == "__main__":
    main()
