# LMS Service Discovery Configuration

This directory configures service discovery for all microservices under `backend/services/`.

## What is configured

- **Service registry**: Consul-based registry contract in `service_registry.yaml`.
- **Health checks**: Every service has a `health_check` block in `discovery_configuration.json`.
- **Registration on startup**: Every service has `startup.register_on_startup: true`.
- **Service lookup**: Inter-service communication is required to use the `discovery://<service-name>` scheme.

## Files

- `service_registry.yaml`: Shared registry + lookup defaults.
- `discovery_configuration.json`: Generated per-service registration + health configuration.
- `internal_service_clients.yaml`: Canonical internal client contract (discovery URI + retry + timeout) for core service-to-service calls.
- `templates/service_startup.env.template`: Startup env contract used by each microservice.
- `scripts/generate_config.py`: Generates discovery config for all services.
- `scripts/verify_config.py`: Verifies registration and discovery requirements.
- `verification_report.json`: Batch verification output.

## Regeneration

```bash
python infrastructure/service-discovery/scripts/generate_config.py
```

## Verification

```bash
python infrastructure/service-discovery/scripts/verify_config.py
```
