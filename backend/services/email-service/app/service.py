from __future__ import annotations

from datetime import datetime, timezone
from string import Template

from fastapi import HTTPException

from .models import DeliveryRecord, DeliveryStatus, EmailTemplate, QueueMessage, TriggerRule
from .schemas import TransactionalEmailRequest, TriggerEventRequest


class EmailService:
    def __init__(self) -> None:
        self.templates: dict[str, EmailTemplate] = {}
        self.trigger_rules: dict[str, TriggerRule] = {}
        self.deliveries: dict[str, DeliveryRecord] = {}
        self.queue: list[QueueMessage] = []
        self._seed_defaults()

    def _seed_defaults(self) -> None:
        defaults = [
            EmailTemplate(
                template_key="welcome_email",
                subject_template="Welcome to LMS, ${first_name}!",
                body_template="Hi ${first_name}, your account is ready for ${tenant_name}.",
                description="Welcome onboarding email",
            ),
            EmailTemplate(
                template_key="password_reset",
                subject_template="Reset your LMS password",
                body_template="Use this link to reset your password: ${reset_link}",
                description="Password reset instructions",
            ),
            EmailTemplate(
                template_key="course_enrollment",
                subject_template="You're enrolled in ${course_name}",
                body_template="Hello ${first_name}, course ${course_name} starts on ${start_date}.",
                description="Enrollment confirmation",
            ),
            EmailTemplate(
                template_key="deadline_reminder",
                subject_template="Reminder: ${course_name} deadline",
                body_template="Assignment ${assignment_name} is due on ${due_date}.",
                description="Learning deadline reminder",
            ),
        ]
        for template in defaults:
            self.templates[template.template_key] = template

        self.trigger_rules["user.created"] = TriggerRule(event_type="user.created", template_key="welcome_email")
        self.trigger_rules["user.password_reset_requested"] = TriggerRule(
            event_type="user.password_reset_requested", template_key="password_reset", default_subject_prefix="Security"
        )
        self.trigger_rules["course.enrollment.created"] = TriggerRule(
            event_type="course.enrollment.created", template_key="course_enrollment"
        )
        self.trigger_rules["learning.deadline.approaching"] = TriggerRule(
            event_type="learning.deadline.approaching", template_key="deadline_reminder", default_subject_prefix="Reminder"
        )

    def upsert_template(self, template: EmailTemplate) -> EmailTemplate:
        existing = self.templates.get(template.template_key)
        if existing:
            existing.subject_template = template.subject_template
            existing.body_template = template.body_template
            existing.description = template.description
            existing.updated_at = datetime.now(timezone.utc)
            return existing
        self.templates[template.template_key] = template
        return template

    def list_templates(self) -> list[EmailTemplate]:
        return list(self.templates.values())

    def set_trigger_rule(self, rule: TriggerRule) -> TriggerRule:
        if rule.template_key not in self.templates:
            raise HTTPException(status_code=404, detail="Template not found for trigger rule")
        self.trigger_rules[rule.event_type] = rule
        return rule

    def list_trigger_rules(self) -> list[TriggerRule]:
        return list(self.trigger_rules.values())

    def queue_transactional_email(self, req: TransactionalEmailRequest) -> DeliveryRecord:
        template = self.templates.get(req.template_key)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        subject = Template(template.subject_template).safe_substitute(req.payload)
        body = Template(template.body_template).safe_substitute(req.payload)

        delivery = DeliveryRecord(
            tenant_id=req.tenant_id,
            template_key=req.template_key,
            recipient_email=req.recipient_email,
            recipient_name=req.recipient_name,
            subject=subject,
            body=body,
            metadata=req.metadata,
            provider=req.provider,
        )
        self.deliveries[delivery.delivery_id] = delivery
        self.queue.append(QueueMessage(delivery_id=delivery.delivery_id))
        return delivery

    def trigger_notification_email(self, req: TriggerEventRequest) -> DeliveryRecord:
        rule = self.trigger_rules.get(req.event_type)
        if not rule:
            raise HTTPException(status_code=404, detail="No email trigger configured for event")

        payload = dict(req.payload)
        if req.recipient_name and "first_name" not in payload:
            payload["first_name"] = req.recipient_name.split(" ")[0]

        delivery = self.queue_transactional_email(
            TransactionalEmailRequest(
                tenant_id=req.tenant_id,
                template_key=rule.template_key,
                recipient_email=req.recipient_email,
                recipient_name=req.recipient_name,
                payload=payload,
                metadata=req.metadata | {"event_type": req.event_type},
                provider=req.provider,
            )
        )

        if rule.default_subject_prefix:
            delivery.subject = f"[{rule.default_subject_prefix}] {delivery.subject}"

        return delivery

    def get_delivery(self, delivery_id: str) -> DeliveryRecord:
        delivery = self.deliveries.get(delivery_id)
        if not delivery:
            raise HTTPException(status_code=404, detail="Delivery record not found")
        return delivery

    def list_deliveries(self, tenant_id: str | None = None, status: DeliveryStatus | None = None) -> list[DeliveryRecord]:
        items = list(self.deliveries.values())
        if tenant_id:
            items = [d for d in items if d.tenant_id == tenant_id]
        if status:
            items = [d for d in items if d.status == status]
        return items

    def get_queue_depth(self) -> tuple[int, list[str]]:
        queued_ids = [msg.delivery_id for msg in self.queue]
        return len(queued_ids), queued_ids

    def process_queue(self, max_batch_size: int = 100) -> tuple[int, int, int]:
        processed = sent = failed = 0

        while self.queue and processed < max_batch_size:
            message = self.queue.pop(0)
            delivery = self.deliveries[message.delivery_id]
            message.attempts += 1
            processed += 1

            if "fail" in delivery.recipient_email:
                delivery.status = DeliveryStatus.FAILED
                delivery.error_message = "Simulated provider rejection"
                delivery.processed_at = datetime.now(timezone.utc)
                failed += 1
                continue

            delivery.status = DeliveryStatus.SENT
            delivery.processed_at = datetime.now(timezone.utc)
            delivery.error_message = None
            sent += 1

        return processed, sent, failed
