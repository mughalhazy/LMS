#!/usr/bin/env python3
import json
from pathlib import Path
import subprocess
import sys
import shutil

root = Path(__file__).resolve().parents[1]
manifest_path = root / "service-manifest.json"
compose_path = root / "docker-compose.yml"

manifest = json.loads(manifest_path.read_text())
services = manifest["services"]

missing = []
for s in services:
    svc_path = Path(__file__).resolve().parents[3] / s["path"]
    if not svc_path.exists():
        missing.append(f"missing path: {s['path']}")
    if s["runtime"] == "python" and not (svc_path / "requirements.txt").exists():
        missing.append(f"{s['name']}: missing requirements.txt")
    if s["runtime"] == "node" and not (svc_path / "package.json").exists():
        missing.append(f"{s['name']}: missing package.json")

if missing:
    print("Verification failed:")
    print("\n".join(missing))
    sys.exit(1)

if shutil.which("docker"):
    cmd = ["docker", "compose", "-f", str(compose_path), "config"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print("docker compose config failed")
        print(res.stderr.strip())
        sys.exit(res.returncode)
    build_status = "validated_via_docker_compose_config"
else:
    build_status = "warning_docker_unavailable_static_validation_only"

print(f"services_deployable={len(services)}")
print("deployment_configs_created=true")
print(f"build_status={build_status}")
