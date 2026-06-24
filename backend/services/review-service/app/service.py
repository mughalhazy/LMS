from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from .models import Review
from .store import InMemoryReviewStore


class ReviewNotFoundError(Exception):
    pass


class ReviewValidationError(Exception):
    pass


class ReviewService:
    def __init__(self, store: InMemoryReviewStore | None = None) -> None:
        self._store = store or InMemoryReviewStore()

    def submit_review(
        self,
        *,
        tenant_id: str,
        course_id: str,
        learner_id: str,
        rating: int,
        body: str,
    ) -> Review:
        if not 1 <= rating <= 5:
            raise ReviewValidationError("rating must be between 1 and 5")
        if not body.strip():
            raise ReviewValidationError("body must not be empty")
        review = Review(
            tenant_id=tenant_id,
            course_id=course_id,
            learner_id=learner_id,
            rating=rating,
            body=body.strip(),
        )
        return self._store.save(review)

    def get_review(self, tenant_id: str, review_id: str) -> Review:
        review = self._store.get(review_id)
        if review is None or review.tenant_id != tenant_id:
            raise ReviewNotFoundError(f"Review {review_id!r} not found")
        return review

    def list_reviews(
        self,
        tenant_id: str,
        course_id: Optional[str] = None,
        learner_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Review]:
        return self._store.list(tenant_id=tenant_id, course_id=course_id, learner_id=learner_id, status=status)

    def approve_review(self, tenant_id: str, review_id: str) -> Review:
        review = self.get_review(tenant_id, review_id)
        review.status = "published"
        review.updated_at = datetime.now(timezone.utc)
        return review

    def reject_review(self, tenant_id: str, review_id: str) -> Review:
        review = self.get_review(tenant_id, review_id)
        review.status = "rejected"
        review.updated_at = datetime.now(timezone.utc)
        return review

    def delete_review(self, tenant_id: str, review_id: str) -> None:
        review = self.get_review(tenant_id, review_id)
        self._store.delete(review.review_id)

    def rating_summary(self, tenant_id: str, course_id: str) -> Dict:
        published = self._store.list(tenant_id=tenant_id, course_id=course_id, status="published")
        if not published:
            return {
                "course_id": course_id,
                "average_rating": 0.0,
                "total_reviews": 0,
                "distribution": {str(i): 0 for i in range(1, 6)},
            }
        avg = round(sum(r.rating for r in published) / len(published), 2)
        distribution = {str(i): sum(1 for r in published if r.rating == i) for i in range(1, 6)}
        return {
            "course_id": course_id,
            "average_rating": avg,
            "total_reviews": len(published),
            "distribution": distribution,
        }
