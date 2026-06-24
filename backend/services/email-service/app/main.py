from fastapi import FastAPI, Query, Depends
from .security import apply_security_headers, require_jwt

from .models import DeliveryStatus, EmailTemplate, TriggerRule
from .schemas import (
    DeliveryListResponse,
    DeliveryOut,
    QueueProcessResponse,
    QueueStateResponse,
    TemplateOut,
    TemplateUpsertRequest,
    TransactionalEmailRequest,
    TriggerEventRequest,
    TriggerRuleRequest,
)
from .service import EmailService

app = FastAPI(title="Email Delivery Service", version="1.0.0", dependencies=[Depends(require_jwt)])


# CAT-004: api-versioning-strategy.md §1 — X-API-Version header required on every response
@app.middleware("http")
async def _add_api_version_header(request, call_next):
    response = await call_next(request)
    response.headers["X-API-Version"] = "v1"
    return response


# FA-024 / G-24: register event consumers on startup
from .consumers import register_consumers as _register_consumers
_register_consumers()


apply_security_headers(app)
service = EmailService()


# Spec: POST /api/v1/email/templates (create/update template)
@app.post("/api/v1/email/templates", response_model=TemplateOut)
@app.put("/api/v1/email/templates/{template_key}", response_model=TemplateOut)
def upsert_template(request: TemplateUpsertRequest, template_key: str = ""):
    key = template_key or getattr(request, "template_key", "")
    template = service.upsert_template(
        EmailTemplate(
            template_key=key,
            subject_template=request.subject_template,
            body_template=request.body_template,
            description=request.description,
        )
    )
    return TemplateOut(**template.model_dump())


@app.get("/api/v1/email/templates", response_model=list[TemplateOut])
def list_templates():
    return [TemplateOut(**t.model_dump()) for t in service.list_templates()]


# Spec: POST /api/v1/email/trigger-rules
@app.post("/api/v1/email/trigger-rules")
@app.put("/api/v1/email/trigger-rules/{event_type}")
def upsert_trigger(request: TriggerRuleRequest, event_type: str = ""):
    key = event_type or getattr(request, "event_type", "")
    rule = service.set_trigger_rule(
        TriggerRule(
            event_type=key,
            template_key=request.template_key,
            default_subject_prefix=request.default_subject_prefix,
        )
    )
    return rule.model_dump()


@app.get("/api/v1/email/trigger-rules")
def list_triggers():
    return [r.model_dump() for r in service.list_trigger_rules()]


# Spec: POST /api/v1/email/send
@app.post("/api/v1/email/send", response_model=DeliveryOut)
def queue_transactional_email(request: TransactionalEmailRequest):
    delivery = service.queue_transactional_email(request)
    return DeliveryOut(**delivery.model_dump())


# Spec: POST /api/v1/email/trigger
@app.post("/api/v1/email/trigger", response_model=DeliveryOut)
def trigger_notification_email(request: TriggerEventRequest):
    delivery = service.trigger_notification_email(request)
    return DeliveryOut(**delivery.model_dump())


# Spec: POST /api/v1/email/queue/process
@app.post("/api/v1/email/queue/process", response_model=QueueProcessResponse)
def process_email_queue(max_batch_size: int = Query(default=100, ge=1, le=1000)):
    processed, sent, failed = service.process_queue(max_batch_size=max_batch_size)
    return QueueProcessResponse(processed_count=processed, sent_count=sent, failed_count=failed)


# Spec: GET /api/v1/email/queue/depth
@app.get("/api/v1/email/queue/depth", response_model=QueueStateResponse)
def get_queue_state():
    depth, queued_ids = service.get_queue_depth()
    return QueueStateResponse(queue_depth=depth, queued_delivery_ids=queued_ids)


# Spec: GET /api/v1/email/deliveries
@app.get("/api/v1/email/deliveries", response_model=DeliveryListResponse)
def list_deliveries(tenant_id: str = Query(...), status: DeliveryStatus | None = Query(default=None)):
    return DeliveryListResponse(
        items=[DeliveryOut(**item.model_dump()) for item in service.list_deliveries(tenant_id=tenant_id, status=status)]
    )


# Spec: GET /api/v1/email/deliveries/{id}
@app.get("/api/v1/email/deliveries/{delivery_id}", response_model=DeliveryOut)
def get_delivery(delivery_id: str, tenant_id: str = Query(...)):
    delivery = service.get_delivery(tenant_id, delivery_id)
    return DeliveryOut(**delivery.model_dump())


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "email-service"}


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "email-service", "service_up": 1}
