from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from .models import DeliveryStatus, IntegrationProvider


class TemplateUpsertRequest(BaseModel):
    template_key: str
    subject_template: str
    body_template: str
    description: str | None = None


class TemplateOut(BaseModel):
    template_key: str
    subject_template: str
    body_template: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class TriggerRuleRequest(BaseModel):
    event_type: str
    template_key: str
    default_subject_prefix: str | None = None


class TriggerEventRequest(BaseModel):
    tenant_id: str
    event_type: str
    recipient_email: str
    recipient_name: str | None = None
    payload: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
    provider: IntegrationProvider = IntegrationProvider.SMTP


class TransactionalEmailRequest(BaseModel):
    tenant_id: str
    template_key: str
    recipient_email: str
    recipient_name: str | None = None
    payload: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, str] = Field(default_factory=dict)
    provider: IntegrationProvider = IntegrationProvider.SMTP


class DeliveryOut(BaseModel):
    delivery_id: str
    tenant_id: str
    template_key: str
    recipient_email: str
    recipient_name: str | None
    subject: str
    body: str
    metadata: dict[str, str]
    status: DeliveryStatus
    provider: IntegrationProvider
    queued_at: datetime
    processed_at: datetime | None
    error_message: str | None


class QueueProcessResponse(BaseModel):
    processed_count: int
    sent_count: int
    failed_count: int


class QueueStateResponse(BaseModel):
    queue_depth: int
    queued_delivery_ids: list[str]


class DeliveryListResponse(BaseModel):
    items: list[DeliveryOut]
