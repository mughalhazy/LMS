# HR Helpdesk Service — Spec

**Service:** `hr-helpdesk-service` | **Gateway:** `/api/v1/hr-helpdesk` | **Port:** varies

## Purpose

Employee HR helpdesk with priority-scored ticket management, SLA tracking, automation hook dispatch, and analytics. Handles HR queries across payroll, benefits, leave, onboarding, compliance, policy, and general categories.

## Responsibilities

- Ticket lifecycle management (create, update, comment, status transitions)
- Automated priority scoring on every ticket write
- SLA risk detection (≤8 hours to due date)
- Automation hook dispatch on ticket events
- Prioritised agent queue
- Analytics snapshot (breakdowns, SLA metrics, automation stats)

## Out of scope

- General IT helpdesk (separate domain)
- HR system of record mutations (payroll, HRIS) — this service tracks the support ticket only

## Data model

| Entity | Fields |
|---|---|
| `HelpdeskTicket` | ticket_id, tenant_id, employee_id, subject, description, category, status, priority, priority_score, priority_factors{}, urgency_level, impacted_employee_count, requested_by_manager, assigned_to, due_at, first_response_at, resolved_at, resolution_summary, reopened_count, tags[], comments[], automation_dispatches[], created_at, updated_at |
| `AutomationHook` | hook_id, tenant_id, name, callback_target, trigger, min_priority, category, statuses[], enabled, created_at |
| `AutomationDispatch` | dispatch_id, tenant_id, hook_id, ticket_id, trigger, callback_target, payload{}, delivered, created_at |

## Category values

`payroll` | `benefits` | `leave` | `onboarding` | `compliance` | `policy` | `general`

## Ticket status lifecycle

`open → triaged → in_progress → waiting_on_employee → resolved → closed`

Resolved/closed tickets can be reopened → `in_progress` (increments `reopened_count`).

## Priority scoring algorithm

Score = sum of:

| Factor | Weight |
|---|---|
| Category weight | payroll: 24, compliance: 22, benefits: 18, leave: 16, onboarding: 14, policy: 10, general: 8 |
| Urgency level | urgency_level × 9 |
| Impact | min(impacted_employee_count, 25) × 1.8 |
| Manager escalation | +8 if requested_by_manager |
| Reopen penalty | reopened_count × 6 |
| SLA risk | +18 if due ≤8h, +10 if due ≤24h |

Priority thresholds: URGENT ≥80, HIGH ≥55, MEDIUM ≥30, LOW <30

Priority recomputed on every ticket write.

## SLA risk

A ticket is SLA-at-risk if: `due_at` is set AND status not resolved/closed AND hours remaining ≤ 8.

## Automation hooks

Triggers: `ticket_created` | `priority_changed` | `sla_at_risk` | `status_changed`

Hook fires if: hook enabled AND trigger matches AND priority ≥ min_priority AND category matches (if set) AND status in hook.statuses (if set).

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/hr-helpdesk/tickets` | Create ticket |
| PATCH | `/api/v1/hr-helpdesk/tickets/{ticketId}` | Update ticket (status, assignment, urgency, etc.) |
| POST | `/api/v1/hr-helpdesk/tickets/{ticketId}/comments` | Add comment |
| GET | `/api/v1/hr-helpdesk/tickets` | List tickets (filter by status, assigned_to) |
| GET | `/api/v1/hr-helpdesk/queue` | Prioritised agent queue (open tickets by score desc) |
| POST | `/api/v1/hr-helpdesk/automation-hooks` | Register automation hook |
| GET | `/api/v1/hr-helpdesk/automation-dispatches` | List dispatches (filter by ticket) |
| GET | `/api/v1/hr-helpdesk/analytics` | Analytics snapshot |

## Behavioral rules

- first_response_at set on first assignment (not on subsequent reassignments)
- Tags are deduped and sorted on every write
- Priority score recomputed automatically — callers do not set priority directly
- Automation dispatch fires synchronously within the ticket write; delivery failures are recorded but do not fail the ticket operation
