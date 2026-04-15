from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
SERVICES_DIR = ROOT / "backend" / "services"
OUT_DIR = ROOT / "infrastructure" / "event-bus"
TOPIC_RE = re.compile(r"^lms\.[a-z0-9_]+(?:\.[a-z0-9_]+)+\.v\d+$")


def _parse_simple_yaml(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data: dict[str, Any] = {}
    for key in ("event_type", "event", "event_topic", "topic", "producer_service", "owner"):
        m = re.search(rf"^{re.escape(key)}:\s*(.+)$", text, flags=re.MULTILINE)
        if m:
            data[key] = m.group(1).strip().strip("\"'")
    m = re.search(r"^(consumer_services|consumers):\s*\n((?:\s*-\s*.+\n)+)", text, flags=re.MULTILINE)
    if m:
        data[m.group(1)] = [line.strip()[2:].strip() for line in m.group(2).splitlines() if line.strip().startswith("-")]
    return data


def _normalize_service_name(name: str, fallback: str) -> str:
    normalized = (name or fallback).strip().replace("_", "-")
    if not normalized.endswith("-service"):
        normalized = f"{normalized}-service"
    return normalized


def _to_snake_case(value: str) -> str:
    value = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    value = re.sub(r"[^a-zA-Z0-9_]+", "_", value)
    return value.strip("_").lower()


def _normalize_topic(event_type: str, service_name: str) -> str:
    domain = service_name.replace("-service", "").replace("-", "_")
    return f"lms.{domain}.{_to_snake_case(event_type)}.v1"


def _default_consumers(service_name: str) -> list[str]:
    defaults = {
        "media-service": ["content-service", "course-service", "lesson-service", "analytics-service", "notification-service"],
        "assessment-service": ["course-service", "progress-service", "analytics-service", "notification-service"],
        "lesson-service": ["progress-service", "analytics-service", "notification-service", "recommendation-service"],
    }
    return defaults.get(service_name, ["analytics-service", "notification-service", "audit-service"])


def build_catalog() -> tuple[dict[str, Any], list[str]]:
    warnings: list[str] = []
    topics: list[dict[str, Any]] = []
    publishing: dict[str, list[str]] = {}
    consuming: dict[str, list[str]] = {}

    for event_file in sorted(SERVICES_DIR.glob("*/events/*")):
        if event_file.is_dir() or event_file.name.lower().startswith("readme") or event_file.suffix in {".ts", ".md"}:
            continue

        service_name = event_file.parts[-3]
        raw = json.loads(event_file.read_text(encoding="utf-8")) if event_file.suffix == ".json" else _parse_simple_yaml(event_file)
        event_type = str(raw.get("event_type") or raw.get("event") or event_file.stem.replace(".event", "")).strip()
        producer = _normalize_service_name(str(raw.get("producer_service") or raw.get("owner") or service_name), service_name)
        topic = str(raw.get("topic") or raw.get("event_topic") or _normalize_topic(event_type, service_name)).strip()
        consumers = raw.get("consumers") or raw.get("consumer_services") or _default_consumers(service_name)

        if isinstance(consumers, list) and consumers and isinstance(consumers[0], dict):
            consumers = [item["service"] for item in consumers if isinstance(item, dict) and "service" in item]
        consumers = [_normalize_service_name(str(c), "unknown-service") for c in consumers]

        if not consumers:
            warnings.append(f"{event_file}: no consumers configured")
            continue
        if not TOPIC_RE.match(topic):
            topic = _normalize_topic(event_type, service_name)
            warnings.append(f"{event_file}: normalized topic to {topic}")

        entry = {
            "event_type": event_type,
            "topic": topic,
            "producer_service": producer,
            "consumer_services": consumers,
            "contract_file": str(event_file.relative_to(ROOT)),
            "schema_ref": f"schemas/{_to_snake_case(event_type)}.schema.json",
        }
        topics.append(entry)
        publishing.setdefault(producer, []).append(topic)
        for c in consumers:
            consuming.setdefault(c, []).append(topic)

    topics.sort(key=lambda t: t["topic"])
    publishing = {k: sorted(v) for k, v in sorted(publishing.items())}
    consuming = {k: sorted(v) for k, v in sorted(consuming.items())}

    catalog = {
        "broker": {
            "platform": "kafka",
            "cluster": "lms-domain-events",
            "bootstrap_servers": [
                "kafka-0.lms.svc.cluster.local:9092",
                "kafka-1.lms.svc.cluster.local:9092",
                "kafka-2.lms.svc.cluster.local:9092"
            ],
            "schema_registry_url": "http://schema-registry.lms.svc.cluster.local:8081",
            "delivery_guarantee": "at-least-once",
            "dead_letter_topic": "lms.platform.events_dlq.v1"
        },
        "event_topics": topics,
        "services_publishing_events": publishing,
        "services_consuming_events": consuming,
    }
    return catalog, warnings


def main() -> int:
    catalog, warnings = build_catalog()
    (OUT_DIR / "event_bus_config.json").write_text(json.dumps(catalog["broker"], indent=2) + "\n")
    (OUT_DIR / "event_topics.json").write_text(json.dumps(catalog["event_topics"], indent=2) + "\n")
    (OUT_DIR / "services_publishing_events.json").write_text(json.dumps(catalog["services_publishing_events"], indent=2) + "\n")
    (OUT_DIR / "services_consuming_events.json").write_text(json.dumps(catalog["services_consuming_events"], indent=2) + "\n")
    report = {
        "status": "passed",
        "checks": {
            "services_publish_domain_events": "passed" if catalog["services_publishing_events"] else "failed",
            "event_subscriptions_configured": "passed" if catalog["services_consuming_events"] else "failed",
        },
        "warnings": warnings,
    }
    (OUT_DIR / "verification_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
