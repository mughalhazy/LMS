from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from .models import AssessmentDefinition, AttemptRecord, SubmissionRecord


class AssessmentStore(Protocol):
    """Storage contract. Backed by service-local persistence only."""

    def create_assessment(self, assessment: AssessmentDefinition) -> AssessmentDefinition: ...

    def get_assessment(self, tenant_id: str, assessment_id: str) -> AssessmentDefinition | None: ...

    def list_assessments(self, tenant_id: str) -> list[AssessmentDefinition]: ...

    def update_assessment(self, assessment: AssessmentDefinition) -> AssessmentDefinition: ...

    def delete_assessment(self, tenant_id: str, assessment_id: str) -> None: ...

    def create_attempt(self, attempt: AttemptRecord) -> AttemptRecord: ...

    def get_attempt(self, tenant_id: str, attempt_id: str) -> AttemptRecord | None: ...

    def list_attempts(self, tenant_id: str, assessment_id: str) -> list[AttemptRecord]: ...

    def update_attempt(self, attempt: AttemptRecord) -> AttemptRecord: ...

    def save_submission(self, submission: SubmissionRecord) -> SubmissionRecord: ...

    def list_submissions(self, tenant_id: str, attempt_id: str) -> list[SubmissionRecord]: ...


class InMemoryAssessmentStore:
    def __init__(self) -> None:
        self._assessments: dict[tuple[str, str], AssessmentDefinition] = {}
        self._attempts: dict[tuple[str, str], AttemptRecord] = {}
        self._submissions: dict[tuple[str, str], list[SubmissionRecord]] = {}

    def create_assessment(self, assessment: AssessmentDefinition) -> AssessmentDefinition:
        key = (assessment.tenant_id, assessment.assessment_id)
        self._assessments[key] = replace(assessment)
        return replace(assessment)

    def get_assessment(self, tenant_id: str, assessment_id: str) -> AssessmentDefinition | None:
        assessment = self._assessments.get((tenant_id, assessment_id))
        return replace(assessment) if assessment else None

    def list_assessments(self, tenant_id: str) -> list[AssessmentDefinition]:
        return [
            replace(item)
            for (item_tenant, _), item in self._assessments.items()
            if item_tenant == tenant_id
        ]

    def update_assessment(self, assessment: AssessmentDefinition) -> AssessmentDefinition:
        key = (assessment.tenant_id, assessment.assessment_id)
        self._assessments[key] = replace(assessment)
        return replace(assessment)

    def delete_assessment(self, tenant_id: str, assessment_id: str) -> None:
        self._assessments.pop((tenant_id, assessment_id), None)

    def create_attempt(self, attempt: AttemptRecord) -> AttemptRecord:
        key = (attempt.tenant_id, attempt.attempt_id)
        self._attempts[key] = replace(attempt)
        return replace(attempt)

    def get_attempt(self, tenant_id: str, attempt_id: str) -> AttemptRecord | None:
        attempt = self._attempts.get((tenant_id, attempt_id))
        return replace(attempt) if attempt else None

    def list_attempts(self, tenant_id: str, assessment_id: str) -> list[AttemptRecord]:
        return [
            replace(item)
            for (item_tenant, _), item in self._attempts.items()
            if item_tenant == tenant_id and item.assessment_id == assessment_id
        ]

    def update_attempt(self, attempt: AttemptRecord) -> AttemptRecord:
        key = (attempt.tenant_id, attempt.attempt_id)
        self._attempts[key] = replace(attempt)
        return replace(attempt)

    def save_submission(self, submission: SubmissionRecord) -> SubmissionRecord:
        key = (submission.tenant_id, submission.attempt_id)
        self._submissions.setdefault(key, []).append(replace(submission))
        return replace(submission)

    def list_submissions(self, tenant_id: str, attempt_id: str) -> list[SubmissionRecord]:
        return [replace(item) for item in self._submissions.get((tenant_id, attempt_id), [])]
