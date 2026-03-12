from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class DeliveryStatus(str, Enum):
    QUEUED = "queued"
    SENT = "sent"
    FAILED = "failed"


class IntegrationProvider(str, Enum):
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    SES = "ses"


class EmailTemplate(BaseModel):
    template_key: str
    subject_template: str
    body_template: str
    description: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DeliveryRecord(BaseModel):
    delivery_id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    template_key: str
    recipient_email: str
    recipient_name: str | None = None
    subject: str
    body: str
    metadata: dict[str, str] = Field(default_factory=dict)
    status: DeliveryStatus = DeliveryStatus.QUEUED
    provider: IntegrationProvider = IntegrationProvider.SMTP
    queued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: datetime | None = None
    error_message: str | None = None


class QueueMessage(BaseModel):
    message_id: str = Field(default_factory=lambda: str(uuid4()))
    delivery_id: str
    enqueued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attempts: int = 0


class TriggerRule(BaseModel):
    event_type: str
    template_key: str
    default_subject_prefix: str | None = None
