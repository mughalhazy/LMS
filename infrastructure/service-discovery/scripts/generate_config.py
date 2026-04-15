from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SERVICES_DIR = ROOT / "backend" / "services"
OUTPUT_FILE = ROOT / "infrastructure" / "service-discovery" / "discovery_configuration.json"


def detect_runtime(service_dir: Path) -> str:
    if (service_dir / "requirements.txt").exists() or (service_dir / "pyproject.toml").exists():
        return "python"
    if any(service_dir.rglob("*.ts")) or (service_dir / "package.json").exists():
        return "node"
    return "unknown"


services: dict[str, dict[str, object]] = {}
for service_dir in sorted(path for path in SERVICES_DIR.iterdir() if path.is_dir()):
    name = service_dir.name
    services[name] = {
        "service_name": name,
        "service_id": f"{name}-${{HOSTNAME}}",
        "registration": {
            "enabled": True,
            "registry": "consul",
            "address_env": "SERVICE_HOST",
            "port_env": "SERVICE_PORT",
            "tags": ["lms", "microservice", name],
        },
        "health_check": {
            "http_path": "/health",
            "interval": "10s",
            "timeout": "2s",
            "deregister_after": "60s",
        },
        "runtime": detect_runtime(service_dir),
        "startup": {
            "register_on_startup": True,
            "deregister_on_shutdown": True,
        },
    }

output = {
    "service_registry": {
        "provider": "consul",
        "address_env": "SERVICE_REGISTRY_ADDRESS",
        "datacenter_env": "SERVICE_REGISTRY_DATACENTER",
    },
    "lookup": {
        "scheme": "discovery://",
        "resolver": "service-registry",
        "cache_ttl": "30s",
        "retry_policy": {
            "max_attempts": 3,
            "backoff": "250ms",
        },
    },
    "services": services,
}

OUTPUT_FILE.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {OUTPUT_FILE}")
print(f"Configured {len(services)} services")
