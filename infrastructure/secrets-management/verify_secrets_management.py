from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERVICES_DIR = ROOT / "backend" / "services"
MAPPING_FILE = ROOT / "infrastructure" / "secrets-management" / "service-secret-mapping.json"
REPORT_FILE = ROOT / "infrastructure" / "secrets-management" / "verification-report.json"

HARDCODED_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"(?i)api[_-]?key\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
    re.compile(r"(?i)(password|passwd|pwd)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"(?i)secret\s*[:=]\s*['\"][^'\"]{12,}['\"]"),
]

SKIP_DIRS = {"node_modules", "__pycache__", ".pytest_cache", "dist", "build", "venv", ".venv"}
CHECK_EXT = {".py", ".ts", ".tsx", ".js", ".json", ".yaml", ".yml"}


def iter_source_files(base: Path):
    for path in base.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in CHECK_EXT:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if "tests" in path.parts:
            continue
        yield path


def find_hardcoded_secrets() -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for file_path in iter_source_files(SERVICES_DIR):
        text = file_path.read_text(encoding="utf-8", errors="ignore")
        for idx, line in enumerate(text.splitlines(), start=1):
            for pattern in HARDCODED_PATTERNS:
                if pattern.search(line):
                    findings.append(
                        {
                            "file": str(file_path.relative_to(ROOT)),
                            "line": idx,
                            "pattern": pattern.pattern,
                        }
                    )
                    break
    return findings


def main() -> int:
    services = sorted([p.name for p in SERVICES_DIR.iterdir() if p.is_dir()])
    mapping = json.loads(MAPPING_FILE.read_text(encoding="utf-8"))
    configured = sorted(mapping.get("services", {}).keys())

    hardcoded = find_hardcoded_secrets()
    missing_from_mapping = sorted(set(services) - set(configured))

    report = {
        "secrets_configured": len(missing_from_mapping) == 0,
        "services_using_secrets": len(configured),
        "security_status": "pass" if not hardcoded and not missing_from_mapping else "fail",
        "missing_service_mappings": missing_from_mapping,
        "hardcoded_secret_findings": hardcoded,
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, indent=2))
    return 0 if report["security_status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
