# Email Service — Spec

**Service:** `email-service` | **Gateway:** `/api/v1/email` | **Port:** varies

## Purpose

Transactional email delivery service. Manages email templates, event-triggered routing rules, delivery queueing, and queue processing. Provider-agnostic with SMTP/SendGrid/SES enum.

## Responsibilities

- Email template management (key-based, subject + body with Python `string.Template` interpolation)
- Event trigger rules (map platform event types to templates)
- Transactional email queueing from direct template invocation
- Event-triggered email routing (event_type → rule → template → queue)
- Queue processing with simulated provider dispatch

## Out of scope

- Push notifications (owned by `push-service`)
- In-app notifications (owned by `notification-service`)
- Email provider SDK wiring (provider field is enum only; actual SDK calls are external)

## Data model

| Entity | Fields |
|---|---|
| `EmailTemplate` | template_key, subject_template, body_template, description, created_at, updated_at |
| `DeliveryRecord` | delivery_id, tenant_id, template_key, recipient_email, recipient_name, subject, body, metadata{}, status, provider, queued_at, processed_at, error_message |
| `TriggerRule` | event_type, template_key, default_subject_prefix |

## Default templates (seeded on startup)

| Key | Trigger event |
|---|---|
| `welcome_email` | `user.created` |
| `password_reset` | `user.password_reset_requested` |
| `course_enrollment` | `course.enrollment.created` |
| `deadline_reminder` | `learning.deadline.approaching` |

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/email/templates` | Create or update template |
| GET | `/api/v1/email/templates` | List all templates |
| POST | `/api/v1/email/trigger-rules` | Register event trigger rule |
| GET | `/api/v1/email/trigger-rules` | List trigger rules |
| POST | `/api/v1/email/send` | Queue transactional email directly |
| POST | `/api/v1/email/trigger` | Route email via event trigger rule |
| GET | `/api/v1/email/deliveries/{deliveryId}` | Get delivery record (tenant-scoped) |
| GET | `/api/v1/email/deliveries` | List deliveries (filter by status) |
| POST | `/api/v1/email/queue/process` | Drain queue (max_batch_size param) |
| GET | `/api/v1/email/queue/depth` | Queue depth |

## Behavioral rules

- Template interpolation uses Python `string.Template.safe_substitute` — missing vars left as-is
- Trigger rule requires template to exist before registration
- Event-triggered emails apply default_subject_prefix as `[prefix] subject` if configured
- Queue processing marks delivered if recipient_email does not contain "fail", otherwise marks failed
- Delivery records are tenant-scoped

## Delivery status

`queued → sent | failed`
