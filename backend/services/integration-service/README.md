# Integration Service

Platform integration service — stateless capability decision orchestration.

## Design reference

`Repo/docs/designs/platform-integration-layer-design.md` | CGAP-078

## Pattern

Implements `B2P08 PlatformIntegrationAPI` — `StatelessDecisionOrchestrator`. All requests are evaluated through a 6-step pipeline:

1. Capability Registry lookup
2. Config Resolution
3. Entitlement Check
4. Feature Flag evaluation
5. Final Decision
6. Usage Metering emit

No state is held between requests. All inputs come from the calling service; all outputs are decision records.

## API

`openapi.yaml` in this directory defines the REST surface.

## Status

Service exists on disk with full implementation. Not yet registered in the API gateway (pending).
