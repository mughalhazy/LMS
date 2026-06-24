from __future__ import annotations

from typing import Dict, List, Optional

from .models import Review


class InMemoryReviewStore:
    def __init__(self) -> None:
        self._reviews: Dict[str, Review] = {}

    def save(self, review: Review) -> Review:
        self._reviews[review.review_id] = review
        return review

    def get(self, review_id: str) -> Optional[Review]:
        return self._reviews.get(review_id)

    def delete(self, review_id: str) -> bool:
        if review_id not in self._reviews:
            return False
        del self._reviews[review_id]
        return True

    def list(
        self,
        tenant_id: str,
        course_id: Optional[str] = None,
        learner_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Review]:
        results = [r for r in self._reviews.values() if r.tenant_id == tenant_id]
        if course_id:
            results = [r for r in results if r.course_id == course_id]
        if learner_id:
            results = [r for r in results if r.learner_id == learner_id]
        if status:
            results = [r for r in results if r.status == status]
        return sorted(results, key=lambda r: r.created_at, reverse=True)
