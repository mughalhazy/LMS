# LMS Event Bus Configuration

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
