# LMS API Gateway Configuration

This directory contains the centralized API Gateway configuration for all LMS backend services.

## Files
- `gateway.yaml`: gateway runtime config, auth middleware, rate limiting, request logging, service registry.
- `routes.yaml`: explicit API-spec routes and catch-all service prefix routes.
- `openapi-aggregate.yaml`: merged OpenAPI surface for gateway-exposed endpoints.
- `verification.md`: verification evidence for service exposure and route-spec alignment.

## Capacity tuning
- `gateway.yaml` now includes replica and runtime scaling knobs for load-test operation (`replicas`, `runtime`).
- Gateway middleware now includes connection pool and response cache settings for high-concurrency workloads.

## Return payload
- `gateway_routes`: `routes.yaml`
- `services_registered`: all backend services in `gateway.yaml` service registry
- `gateway_configuration_files`: `gateway.yaml`, `routes.yaml`, `openapi-aggregate.yaml`, `verification.md`
