# interaction-layer-service

Conversational interaction layer for all personas (learner/operator/manager/instructor). Builds action-embedded outbound messages (BC-INT-01), handles idempotent action replies, maintains stateful conversation sessions with persona-aware command shortcuts (BC-INT-02), and sends role-specific onboarding messages for new users (B15-023). Spec: `docs/specs/interaction-layer-spec.md` (MS§5.9).

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/interaction/sessions` | Create or retrieve conversation session |
| POST | `/api/v1/interaction/messages` | Build action-embedded outbound message (BC-INT-01) |
| POST | `/api/v1/interaction/replies` | Handle inbound reply — idempotent action dispatch |
| POST | `/api/v1/interaction/onboarding` | Send role-specific onboarding message (BC-INT-02 — B15-023) |
| GET | `/api/v1/interaction/personas/{persona}` | List available commands for a persona |
| GET | `/health` | Health check |

## B15 fixes (2026-06-02)

- **B15-023**: `send_onboarding_message()` added — BC-INT-02 compliance; new users receive role-specific onboarding explaining available commands per persona (learner/operator/manager/instructor)

## Gateway

Route: `/api/v1/interaction` | Rate limit: `public-api-standard`
