# LMS Event Bus Configuration

> **Runtime status:** The event bus runs **in-memory** in the current runtime. `event_bus_config.json` references a Kafka cluster configuration, but no Kafka broker is wired in the actual running environment. The JSON files in this directory are **spec artifacts** — they define the intended event topology, topic catalog, and producer/consumer contracts for future infrastructure wiring. Do not treat them as running infrastructure configuration.

This directory contains the LMS domain-event bus configuration generated from service event contracts under `backend/services/*/events`.

## Files

- `event_bus_config.json`: broker-level configuration (Kafka cluster, delivery semantics, schema registry, DLQ topic).
- `event_topics.json`: normalized topic catalog with producer/consumer mapping and source contract file.
- `services_publishing_events.json`: map of services that publish domain events.
- `services_consuming_events.json`: map of services subscribed to domain-event topics.
- `verification_report.json`: verification output confirming publication and subscription configuration checks.
- `schemas/*.schema.json`: JSON Schemas for event envelope and topic-definition validation.
- `validate_event_bus.py`: generation + validation script.

## Regeneration

```bash
python infrastructure/event-bus/validate_event_bus.py
```
