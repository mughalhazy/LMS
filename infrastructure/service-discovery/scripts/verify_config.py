from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = ROOT / "backend" / "services"
CONFIG_PATH = ROOT / "infrastructure" / "service-discovery" / "discovery_configuration.json"

config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
configured = set(config["services"].keys())
actual = {path.name for path in SERVICES_DIR.iterdir() if path.is_dir()}

missing = sorted(actual - configured)
extra = sorted(configured - actual)

if missing or extra:
    raise SystemExit(
        "Configuration mismatch:\n"
        f" - missing: {missing}\n"
        f" - extra: {extra}"
    )

health_failures = [
    name
    for name, service_cfg in config["services"].items()
    if not service_cfg.get("health_check", {}).get("http_path")
]
if health_failures:
    raise SystemExit(f"Missing health check path for: {health_failures}")

startup_failures = [
    name
    for name, service_cfg in config["services"].items()
    if not service_cfg.get("startup", {}).get("register_on_startup")
]
if startup_failures:
    raise SystemExit(f"Startup registration is disabled for: {startup_failures}")

hardcoded_targets = []
for name, service_cfg in config["services"].items():
    dependencies = service_cfg.get("dependencies", [])
    for dependency in dependencies:
        if isinstance(dependency, str) and dependency.startswith(("http://", "https://")):
            hardcoded_targets.append((name, dependency))

if hardcoded_targets:
    raise SystemExit(f"Hardcoded service URLs found: {hardcoded_targets}")

print(f"All services are configured for discovery: {len(actual)}")
print("Health checks configured for all services")
print("Startup registration enabled for all services")
print("No hardcoded service URLs in discovery dependencies")
