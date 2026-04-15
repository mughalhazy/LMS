#!/usr/bin/env python3
import json
import re
import shutil
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
MANIFEST_PATH = ROOT / "service-manifest.json"
COMPOSE_PATH = ROOT / "docker-compose.yml"
START_SCRIPT_PATH = ROOT / "scripts" / "start-service.sh"
SECRETS_MAPPING_PATH = REPO_ROOT / "infrastructure" / "secrets-management" / "service-secret-mapping.json"
COMMON_ENV_PATH = ROOT / "env" / "common.env"
SERVICES_ENV_PATH = ROOT / "env" / "services.env"

REQUIRED_COMMON_ENV = {"DATABASE_URL", "REDIS_URL", "EVENT_BUS_URL", "OTEL_EXPORTER_OTLP_ENDPOINT"}
REQUIRED_SECRET_ENV = {"JWT_SHARED_SECRET", "DATABASE_URL", "SERVICE_API_KEY", "ENCRYPTION_KEY"}


def load_json(path: Path):
    return json.loads(path.read_text())


def parse_env_file(path: Path) -> set[str]:
    keys = set()
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        keys.add(line.split("=", 1)[0].strip())
    return keys


def parse_compose_services(compose_text: str) -> dict:
    services: dict[str, dict] = {}
    block_pattern = re.compile(r"^  ([a-z0-9-]+):\n((?:^(?:    |      |        ).*\n?)*)", re.M)

    for service_name, block in block_pattern.findall(compose_text):
        if service_name in {"services", "networks", "volumes"}:
            continue

        dockerfile_match = re.search(r"(?m)^      dockerfile:\s*(.+)$", block)
        env_files = [m.strip() for m in re.findall(r"(?m)^      -\s*(.+)$", re.search(r"(?ms)^    env_file:\n(.*?)(?=^    [a-z_]+:|\Z)", block).group(1))] if re.search(r"(?ms)^    env_file:\n(.*?)(?=^    [a-z_]+:|\Z)", block) else []
        ports = [m.strip().strip('"') for m in re.findall(r"(?m)^      -\s*(.+)$", re.search(r"(?ms)^    ports:\n(.*?)(?=^    [a-z_]+:|\Z)", block).group(1))] if re.search(r"(?ms)^    ports:\n(.*?)(?=^    [a-z_]+:|\Z)", block) else []

        environment = {}
        env_block_match = re.search(r"(?ms)^    environment:\n(.*?)(?=^    [a-z_]+:|\Z)", block)
        if env_block_match:
            for line in env_block_match.group(1).splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("-") or ":" not in stripped:
                    continue
                key, value = stripped.split(":", 1)
                environment[key.strip()] = value.strip().strip('"')

        services[service_name] = {
            "env_file": env_files,
            "environment": environment,
            "ports": ports,
            "dockerfile": dockerfile_match.group(1).strip() if dockerfile_match else "",
        }

    return services


def check_start_command(service_path: Path, command: str) -> bool:
    package_json = service_path / "package.json"
    if not package_json.exists():
        return False
    pkg = load_json(package_json)
    scripts = pkg.get("scripts", {})
    normalized = " ".join(command.strip().split())
    return normalized == "npm run start" and "start" in scripts


def main() -> int:
    manifest = load_json(MANIFEST_PATH)
    compose_services = parse_compose_services(COMPOSE_PATH.read_text())
    secrets_mapping = load_json(SECRETS_MAPPING_PATH).get("services", {})
    common_env_keys = parse_env_file(COMMON_ENV_PATH)

    services = manifest.get("services", [])
    checks: list[tuple[str, bool, list[str]]] = []
    build_issues, env_issues, secret_issues, port_issues, startup_issues = [], [], [], [], []
    seen_ports = {}

    for service in services:
        name = service["name"]
        runtime = service["runtime"]
        service_path = REPO_ROOT / service["path"]
        compose_service = compose_services.get(name)

        if not service_path.exists():
            build_issues.append(f"{name}: service path missing ({service['path']})")
            continue
        if runtime == "python" and not (service_path / "requirements.txt").exists():
            build_issues.append(f"{name}: missing requirements.txt")
        if runtime == "node" and not (service_path / "package.json").exists():
            build_issues.append(f"{name}: missing package.json")

        if compose_service is None:
            build_issues.append(f"{name}: missing docker-compose service")
            continue

        dockerfile = compose_service.get("dockerfile", "")
        if runtime == "python" and not dockerfile.endswith("Dockerfile.python"):
            build_issues.append(f"{name}: expected Dockerfile.python, found {dockerfile}")
        if runtime == "node" and not dockerfile.endswith("Dockerfile.node"):
            build_issues.append(f"{name}: expected Dockerfile.node, found {dockerfile}")

        env_files = set(compose_service.get("env_file", []))
        for required_env in {"./env/common.env", "./env/services.env"}:
            if required_env not in env_files:
                env_issues.append(f"{name}: missing env_file {required_env}")

        service_env = compose_service.get("environment", {})
        if service_env.get("SERVICE_NAME", "") != name:
            env_issues.append(f"{name}: SERVICE_NAME mismatch")

        manifest_port = str(service["port"])
        if service_env.get("SERVICE_PORT", "") != manifest_port:
            port_issues.append(f"{name}: SERVICE_PORT mismatch ({service_env.get('SERVICE_PORT')} != {manifest_port})")

        expected_binding = f"{manifest_port}:{manifest_port}"
        if expected_binding not in compose_service.get("ports", []):
            port_issues.append(f"{name}: missing port binding {expected_binding}")

        if manifest_port in seen_ports:
            port_issues.append(f"{name}: duplicate port {manifest_port} also used by {seen_ports[manifest_port]}")
        else:
            seen_ports[manifest_port] = name

        app_module = service_env.get("APP_MODULE", "").strip()
        start_command = service_env.get("START_COMMAND", "").strip()

        if runtime == "python":
            if not app_module:
                startup_issues.append(f"{name}: python service missing APP_MODULE")
            if app_module and not (service_path / "app" / "main.py").exists():
                startup_issues.append(f"{name}: app/main.py missing")
            if start_command:
                startup_issues.append(f"{name}: python START_COMMAND must be empty")
        else:
            if app_module:
                startup_issues.append(f"{name}: node APP_MODULE must be empty")
            if not start_command:
                startup_issues.append(f"{name}: node START_COMMAND missing")
            elif not check_start_command(service_path, start_command):
                startup_issues.append(f"{name}: START_COMMAND not backed by package.json start script")

        mapping = secrets_mapping.get(name)
        if not mapping:
            secret_issues.append(f"{name}: missing secrets mapping entry")
        else:
            missing_secret_keys = REQUIRED_SECRET_ENV - set(mapping.get("environment", {}))
            if missing_secret_keys:
                secret_issues.append(f"{name}: missing secret env keys {sorted(missing_secret_keys)}")

    if not REQUIRED_COMMON_ENV.issubset(common_env_keys):
        env_issues.append(f"common.env missing keys: {sorted(REQUIRED_COMMON_ENV - common_env_keys)}")
    if not SERVICES_ENV_PATH.exists():
        env_issues.append("services.env file missing")

    if not START_SCRIPT_PATH.exists():
        startup_issues.append("start-service.sh missing")
    else:
        text = START_SCRIPT_PATH.read_text()
        for token in ["APP_MODULE", "START_COMMAND", "uvicorn", "exec"]:
            if token not in text:
                startup_issues.append(f"start-service.sh missing token: {token}")
        if not (START_SCRIPT_PATH.stat().st_mode & stat.S_IXUSR):
            startup_issues.append("start-service.sh not executable")

    checks.append(("container_builds", len(build_issues) == 0, build_issues))
    checks.append(("service_environment", len(env_issues) == 0, env_issues))
    checks.append(("secrets_injection", len(secret_issues) == 0, secret_issues))
    checks.append(("service_ports", len(port_issues) == 0, port_issues))
    checks.append(("startup_scripts", len(startup_issues) == 0, startup_issues))

    startup_validation = "static_startup_validation"
    if shutil.which("docker"):
        res = subprocess.run(["docker", "compose", "-f", str(COMPOSE_PATH), "config"], capture_output=True, text=True)
        if res.returncode != 0:
            checks.append(("compose_config", False, [res.stderr.strip()]))
        else:
            checks.append(("compose_config", True, []))
            startup_validation = "docker_compose_config"

    failed = [(name, issues) for name, ok, issues in checks if not ok]
    passed_count = sum(1 for _, ok, _ in checks if ok)
    score = int(round((passed_count / len(checks)) * 10)) if checks else 0

    print(f"services_deployed={len(services)}")
    print("deployment_issues_fixed=0")
    print(f"deployment_score={score}/10")
    print(f"startup_validation={startup_validation}")

    if failed:
        for check_name, issues in failed:
            print(f"failed_check={check_name}")
            for issue in issues:
                print(f"issue={issue}")
        return 1

    print("all_checks_passed=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
