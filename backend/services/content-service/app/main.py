"""Content service API entrypoint."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from .security import apply_security_headers, require_jwt
from .service import ContentManagementService, ContentNotFoundError, AccessDeniedError

app = FastAPI(title="Content Service", version="0.1.0", dependencies=[Depends(require_jwt)])


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

_content_svc = ContentManagementService()


class ContentUploadRequest(BaseModel):
    tenant_id: str = Field(min_length=1)
    course_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    content_type: Literal["video", "audio", "document", "scorm_package", "assessment_asset"]


class ContentMetadataUpdateRequest(BaseModel):
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    language: str | None = None
    duration_seconds: int | None = None
    license: str | None = None
    accessibility_notes: str | None = None
    visibility: Literal["private", "tenant", "public"] | None = None
    allowed_roles: list[str] | None = None
    allowed_user_ids: list[str] | None = None


class ContentUploadResponse(BaseModel):
    content_id: str
    tenant_id: str
    course_id: str
    title: str
    content_type: str
    status: Literal["uploaded"]


class ContentRetrieveResponse(BaseModel):
    content_id: str
    tenant_id: str
    title: str
    content_type: str
    description: str | None
    language: str | None
    duration_seconds: int | None
    active_version: int
    delivery_url: str
    tags: list[str]
    visibility: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/content/uploads", response_model=ContentUploadResponse)
def upload_content(request: ContentUploadRequest) -> ContentUploadResponse:
    return ContentUploadResponse(
        content_id=f"cnt-{uuid4().hex[:10]}",
        tenant_id=request.tenant_id,
        course_id=request.course_id,
        title=request.title,
        content_type=request.content_type,
        status="uploaded",
    )

@app.get("/api/v1/content/{content_id}", response_model=ContentRetrieveResponse)
def get_content(
    content_id: str,
    tenant_id: str = Query(min_length=1),
    requester_user_id: str = Query(default="system"),
    requester_roles: str = Query(default=""),
) -> ContentRetrieveResponse:
    """Fetch content by content_id with access enforcement and secure delivery URL.

    Spec: docs/specs/features/content-service-spec.md — retrieve_content operation.
    """
    try:
        result = _content_svc.get_content(
            tenant_id=tenant_id,
            content_id=content_id,
            requester_user_id=requester_user_id,
            requester_roles=[r for r in requester_roles.split(",") if r],
        )
    except ContentNotFoundError:
        raise HTTPException(status_code=404, detail=f"content_id={content_id!r} not found")
    except AccessDeniedError:
        raise HTTPException(status_code=403, detail="Access denied to requested content")

    record = result["metadata"]
    return ContentRetrieveResponse(
        content_id=record.content_id,
        tenant_id=record.tenant_id,
        title=record.title,
        content_type=record.content_type.value,
        description=record.description,
        language=record.language,
        duration_seconds=record.duration_seconds,
        active_version=record.active_version,
        delivery_url=result["delivery_url"],
        tags=record.tags,
        visibility=record.visibility.value,
    )


@app.get("/api/v1/content")
def list_content(
    tenant_id: str = Query(min_length=1),
    requester_user_id: str = Query(default="system"),
    requester_roles: str = Query(default=""),
    content_type: str | None = Query(default=None),
    tags: str | None = Query(default=None),
    language: str | None = Query(default=None),
) -> dict:
    # Spec: content_service_spec.md — list_content with access filtering
    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else None
    results = _content_svc.list_content(
        tenant_id=tenant_id,
        requester_user_id=requester_user_id,
        requester_roles=[r for r in requester_roles.split(",") if r],
        content_type=content_type,
        tags=tag_list,
        language=language,
    )
    return {
        "content": [
            {
                "content_id": r.content_id,
                "title": r.title,
                "content_type": r.content_type.value,
                "visibility": r.visibility.value,
                "language": r.language,
                "tags": r.tags,
                "active_version": r.active_version,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
            }
            for r in results
        ],
        "total": len(results),
    }


@app.patch("/api/v1/content/{content_id}/metadata", response_model=ContentRetrieveResponse)
def update_content_metadata(
    content_id: str,
    request: ContentMetadataUpdateRequest,
    tenant_id: str = Query(min_length=1),
    requester_user_id: str = Query(default="system"),
) -> ContentRetrieveResponse:
    # Spec: content_service_spec.md — update_metadata operation
    try:
        record = _content_svc.update_metadata(
            tenant_id=tenant_id,
            content_id=content_id,
            title=request.title,
            description=request.description,
            tags=request.tags,
            language=request.language,
            duration_seconds=request.duration_seconds,
            license=request.license,
            accessibility_notes=request.accessibility_notes,
            visibility=request.visibility,
            allowed_roles=request.allowed_roles,
            allowed_user_ids=request.allowed_user_ids,
        )
    except ContentNotFoundError:
        raise HTTPException(status_code=404, detail=f"content_id={content_id!r} not found")
    return ContentRetrieveResponse(
        content_id=record.content_id,
        tenant_id=record.tenant_id,
        title=record.title,
        content_type=record.content_type.value,
        description=record.description,
        language=record.language,
        duration_seconds=record.duration_seconds,
        active_version=record.active_version,
        delivery_url=f"/content/{content_id}/stream?tenant={tenant_id}&v={record.active_version}",
        tags=record.tags,
        visibility=record.visibility.value,
    )


@app.get("/metrics")
def metrics() -> dict[str, int | str]:
    return {"service": "content-service", "service_up": 1}


# ── Content versioning (content-versioning-spec.md) ───────────────────────────
# B04-001: service.py implements all 5 versioning methods but main.py had no routes

class CreateVersionRequest(BaseModel):
    change_summary: str
    editor_id: str
    source_version: int | None = None
    checksum_sha256: str = ""
    metadata_updates: dict[str, Any] | None = None


class RollbackVersionRequest(BaseModel):
    rollback_reason: str
    requested_by: str


class PublishVersionRequest(BaseModel):
    publisher_id: str
    release_notes: str = ""
    publish_scope: str = "global"


class VersionResponse(BaseModel):
    version_id: str
    content_id: str
    version_number: int
    status: str
    change_summary: str
    editor_id: str
    created_at: datetime
    published_at: datetime | None = None
    publisher_id: str | None = None
    release_notes: str | None = None
    rollback_origin_version: int | None = None


def _version_to_response(v: Any) -> VersionResponse:
    return VersionResponse(
        version_id=v.version_id,
        content_id=v.content_id,
        version_number=v.version_number,
        status=v.status.value,
        change_summary=v.change_summary,
        editor_id=v.editor_id,
        created_at=v.created_at,
        published_at=v.published_at,
        publisher_id=v.publisher_id,
        release_notes=v.release_notes,
        rollback_origin_version=v.rollback_origin_version,
    )


@app.post("/api/v1/content/{content_id}/versions", status_code=201, response_model=VersionResponse)
def create_version(
    content_id: str,
    request: CreateVersionRequest,
    tenant_id: str = Query(min_length=1),
) -> VersionResponse:
    # B04-001: content-versioning-spec.md — version creation operation
    from .service import VersionError
    try:
        v = _content_svc.create_version(
            tenant_id=tenant_id,
            content_id=content_id,
            change_summary=request.change_summary,
            editor_id=request.editor_id,
            checksum_sha256=request.checksum_sha256,
            source_version=request.source_version,
            metadata_updates=request.metadata_updates,
        )
    except ContentNotFoundError:
        raise HTTPException(status_code=404, detail=f"content_id={content_id!r} not found")
    except VersionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _version_to_response(v)


@app.get("/api/v1/content/{content_id}/versions", response_model=list[VersionResponse])
def list_versions(
    content_id: str,
    tenant_id: str = Query(min_length=1),
) -> list[VersionResponse]:
    # B04-001: content-versioning-spec.md — list all versions for a content asset
    try:
        versions = _content_svc.list_versions(tenant_id=tenant_id, content_id=content_id)
    except ContentNotFoundError:
        raise HTTPException(status_code=404, detail=f"content_id={content_id!r} not found")
    return [_version_to_response(v) for v in versions]


@app.get("/api/v1/content/{content_id}/versions/{version_number}", response_model=VersionResponse)
def get_version(
    content_id: str,
    version_number: int,
    tenant_id: str = Query(min_length=1),
) -> VersionResponse:
    # B04-001: content-versioning-spec.md — get a specific version
    from .service import VersionError
    try:
        v = _content_svc.get_version(tenant_id=tenant_id, content_id=content_id, version_number=version_number)
    except ContentNotFoundError:
        raise HTTPException(status_code=404, detail=f"content_id={content_id!r} not found")
    except VersionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _version_to_response(v)


@app.post("/api/v1/content/{content_id}/versions/{version_number}/rollback", status_code=201, response_model=VersionResponse)
def rollback_version(
    content_id: str,
    version_number: int,
    request: RollbackVersionRequest,
    tenant_id: str = Query(min_length=1),
) -> VersionResponse:
    # B04-001: content-versioning-spec.md — version rollback operation
    from .service import VersionError
    try:
        v = _content_svc.rollback_version(
            tenant_id=tenant_id,
            content_id=content_id,
            target_version_number=version_number,
            rollback_reason=request.rollback_reason,
            requested_by=request.requested_by,
        )
    except ContentNotFoundError:
        raise HTTPException(status_code=404, detail=f"content_id={content_id!r} not found")
    except VersionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _version_to_response(v)


@app.post("/api/v1/content/{content_id}/versions/{version_number}/publish", response_model=VersionResponse)
def publish_version(
    content_id: str,
    version_number: int,
    request: PublishVersionRequest,
    tenant_id: str = Query(min_length=1),
) -> VersionResponse:
    # B04-001: content-versioning-spec.md — version publishing operation
    from .service import VersionError
    try:
        v = _content_svc.publish_version(
            tenant_id=tenant_id,
            content_id=content_id,
            version_number=version_number,
            publisher_id=request.publisher_id,
            release_notes=request.release_notes,
            publish_scope=request.publish_scope,
        )
    except ContentNotFoundError:
        raise HTTPException(status_code=404, detail=f"content_id={content_id!r} not found")
    except VersionError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return _version_to_response(v)

