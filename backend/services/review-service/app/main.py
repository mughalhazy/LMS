"""Service entrypoint — review-service REST API."""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.responses import Response

from .schemas import ReviewResponse, RatingSummaryResponse, SubmitReviewRequest
from .security import apply_security_headers, require_jwt
from .service import ReviewNotFoundError, ReviewService, ReviewValidationError

# B13-004: multi-tenant-isolation-model §2 — JWT required
app = FastAPI(title="review-service", version="1.0.0", dependencies=[Depends(require_jwt)])


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
_SERVICE = ReviewService()


def _tenant_context(
    x_tenant_id: Annotated[str | None, Header()] = None,
    x_actor_id: Annotated[str | None, Header()] = None,
) -> tuple[str, str]:
    if not x_tenant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_tenant_id")
    return x_tenant_id, x_actor_id or "system"


def _review_to_response(review) -> dict:
    return ReviewResponse(
        review_id=review.review_id,
        tenant_id=review.tenant_id,
        course_id=review.course_id,
        learner_id=review.learner_id,
        rating=review.rating,
        body=review.body,
        status=review.status,
        created_at=review.created_at,
        updated_at=review.updated_at,
    ).model_dump()


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "review-service"}


@app.get("/metrics")
def metrics() -> dict:
    return {"service": "review-service", "service_up": 1}


@app.post("/api/v1/reviews", status_code=status.HTTP_201_CREATED)
def submit_review(
    request: SubmitReviewRequest,
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    try:
        review = _SERVICE.submit_review(
            tenant_id=tenant_id,
            course_id=request.course_id,
            learner_id=request.learner_id,
            rating=request.rating,
            body=request.body,
        )
    except ReviewValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    return _review_to_response(review)


@app.get("/api/v1/reviews")
def list_reviews(
    course_id: Optional[str] = Query(default=None),
    learner_id: Optional[str] = Query(default=None),
    review_status: Optional[str] = Query(default=None, alias="status"),
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    reviews = _SERVICE.list_reviews(
        tenant_id=tenant_id,
        course_id=course_id,
        learner_id=learner_id,
        status=review_status,
    )
    return {"reviews": [_review_to_response(r) for r in reviews], "total": len(reviews)}


@app.get("/api/v1/reviews/{review_id}")
def get_review(review_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    tenant_id, _ = ctx
    try:
        return _review_to_response(_SERVICE.get_review(tenant_id, review_id))
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post("/api/v1/reviews/{review_id}:approve")
def approve_review(review_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    tenant_id, _ = ctx
    try:
        return _review_to_response(_SERVICE.approve_review(tenant_id, review_id))
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.post("/api/v1/reviews/{review_id}:reject")
def reject_review(review_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> dict:
    tenant_id, _ = ctx
    try:
        return _review_to_response(_SERVICE.reject_review(tenant_id, review_id))
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@app.delete("/api/v1/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(review_id: str, ctx: tuple[str, str] = Depends(_tenant_context)) -> Response:
    tenant_id, _ = ctx
    try:
        _SERVICE.delete_review(tenant_id, review_id)
    except ReviewNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/v1/ratings", response_model=RatingSummaryResponse)
def rating_summary(
    course_id: str = Query(...),
    ctx: tuple[str, str] = Depends(_tenant_context),
) -> dict:
    tenant_id, _ = ctx
    return _SERVICE.rating_summary(tenant_id=tenant_id, course_id=course_id)
