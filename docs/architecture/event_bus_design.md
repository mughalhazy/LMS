event_topic
producer_service
consumer_services
purpose

lms.employee.created.v1
employee-service
identity-service, payroll-service, org-structure-service, notification-service, audit-service
Primary domain event for new employee onboarding. Published asynchronously via transactional outbox to guarantee at-least-once delivery and preserve producer/consumer decoupling.

lms.employee.updated.v1
employee-service
identity-service, payroll-service, org-structure-service, compliance-service, audit-service
Domain event for employee profile or organizational changes. Versioned topic enables schema evolution without breaking existing consumers.

lms.employee.terminated.v1
employee-service
identity-service, payroll-service, access-control-service, asset-service, notification-service, audit-service
Domain event that triggers asynchronous offboarding workflows across security, finance, and asset recovery services.

lms.leave.requested.v1
leave-service
approval-service, workforce-planning-service, notification-service, audit-service
Domain event emitted when leave is submitted. Reliable asynchronous fan-out allows independent approval and staffing impact processing.

lms.leave.approved.v1
approval-service
leave-service, payroll-service, workforce-planning-service, notification-service
Domain event for approved leave decisions, ensuring downstream systems update balances, payroll, and schedules without synchronous coupling.

lms.payroll.disbursed.v1
payroll-service
finance-service, reporting-service, notification-service, audit-service
Domain event signaling completed payroll payouts. Supports eventual consistency and replay for reconciliation consumers.

lms.training.completed.v1
learning-service
employee-service, compliance-service, reporting-service, notification-service
Domain event for completed learning activity, enabling asynchronous profile updates and compliance evidence capture.

lms.events.retry.v1
event-delivery-service
all original subscribed consumer services
Internal reliability topic for exponential backoff retries when consumer processing fails transiently; preserves at-least-once delivery semantics.

lms.events.dlq.v1
event-delivery-service
operations-service, audit-service, owning-domain-service
Dead-letter topic for poison messages after retry exhaustion. Enables operational recovery, auditability, and safe reprocessing workflows.

lms.schema.changed.v1
schema-registry-service
all producer services, all consumer services
Governance event announcing new schema versions and deprecation windows so producers/consumers can migrate safely while maintaining backward compatibility.
