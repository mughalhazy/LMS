from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Dict, List, Optional
from uuid import uuid4

from .models import (
    Assessment,
    AssessmentStatus,
    AssessmentType,
    AuditEvent,
    Difficulty,
    GradingRule,
    QuestionBank,
    QuestionItem,
)
from .repository import InMemoryAssessmentRepository


class AssessmentServiceError(Exception):
    pass


class AssessmentNotFoundError(AssessmentServiceError):
    pass


class TenantScopeError(AssessmentServiceError):
    pass


class AssessmentPublishValidationError(AssessmentServiceError):
    pass


class AssessmentService:
    def __init__(self, repository: InMemoryAssessmentRepository) -> None:
        self.repository = repository

    def create_assessment(
        self,
        *,
        tenant_id: str,
        course_id: str,
        title: str,
        description: str,
        assessment_type: str,
        time_limit_minutes: int,
        created_by: str,
        lesson_id: Optional[str] = None,
        question_bank_id: Optional[str] = None,
        grading_rule_id: Optional[str] = None,
    ) -> Dict:
        if time_limit_minutes < 1:
            raise AssessmentServiceError("time_limit_minutes must be at least 1")

        if question_bank_id:
            self._get_tenant_question_bank(tenant_id=tenant_id, question_bank_id=question_bank_id)
        if grading_rule_id:
            self._get_tenant_grading_rule(tenant_id=tenant_id, grading_rule_id=grading_rule_id)

        assessment = Assessment(
            assessment_id=str(uuid4()),
            tenant_id=tenant_id,
            course_id=course_id,
            lesson_id=lesson_id,
            title=title,
            description=description,
            assessment_type=AssessmentType(assessment_type),
            time_limit_minutes=time_limit_minutes,
            question_bank_id=question_bank_id,
            grading_rule_id=grading_rule_id,
            created_by=created_by,
        )
        self.repository.create_assessment(assessment)
        self._audit("AssessmentCreated", assessment.assessment_id, tenant_id, {"course_id": course_id})

        return {
            "assessment_id": assessment.assessment_id,
            "status": assessment.status.value,
            "course_id": assessment.course_id,
            "question_bank_id": assessment.question_bank_id,
            "grading_rule_id": assessment.grading_rule_id,
            "audit_event": "AssessmentCreated",
        }

    def create_question_bank(
        self,
        *,
        tenant_id: str,
        name: str,
        description: str,
        created_by: str,
        course_id: Optional[str] = None,
    ) -> Dict:
        question_bank = QuestionBank(
            question_bank_id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            description=description,
            course_id=course_id,
            created_by=created_by,
        )
        self.repository.create_question_bank(question_bank)
        self._audit("QuestionBankCreated", question_bank.question_bank_id, tenant_id, {"name": name})

        return {
            "question_bank_id": question_bank.question_bank_id,
            "name": question_bank.name,
            "course_id": question_bank.course_id,
            "audit_event": "QuestionBankCreated",
        }

    def add_question_bank_item(
        self,
        *,
        tenant_id: str,
        question_bank_id: str,
        prompt: str,
        question_type: str,
        options: List[str],
        correct_answer: str,
        objective_tag: str,
        difficulty: str,
        points: float,
        metadata: Optional[Dict[str, str]] = None,
    ) -> Dict:
        if points <= 0:
            raise AssessmentServiceError("question points must be greater than 0")

        question_bank = self._get_tenant_question_bank(tenant_id=tenant_id, question_bank_id=question_bank_id)

        if question_type in {"single_choice", "multiple_choice"} and correct_answer not in options:
            raise AssessmentServiceError("correct_answer must exist in options for choice questions")

        question_item = QuestionItem(
            question_id=str(uuid4()),
            tenant_id=tenant_id,
            prompt=prompt,
            question_type=question_type,
            options=options,
            correct_answer=correct_answer,
            objective_tag=objective_tag,
            difficulty=Difficulty(difficulty),
            points=points,
            metadata=metadata or {},
        )
        updated = replace(
            question_bank,
            questions=[*question_bank.questions, question_item],
            updated_at=datetime.utcnow(),
        )
        self.repository.update_question_bank(updated)
        self._audit("QuestionBankItemAdded", question_bank_id, tenant_id, {"question_id": question_item.question_id})

        return {
            "question_id": question_item.question_id,
            "question_bank_id": question_bank_id,
            "question_count": len(updated.questions),
            "audit_event": "QuestionBankItemAdded",
        }

    def create_grading_rule(
        self,
        *,
        tenant_id: str,
        name: str,
        pass_threshold: float,
        negative_marking_ratio: float,
        max_attempts: int,
        allow_partial_credit: bool,
        late_penalty_percent: float,
        created_by: str,
    ) -> Dict:
        if pass_threshold < 0 or pass_threshold > 100:
            raise AssessmentServiceError("pass_threshold must be between 0 and 100")
        if negative_marking_ratio < 0 or negative_marking_ratio > 1:
            raise AssessmentServiceError("negative_marking_ratio must be between 0 and 1")
        if max_attempts < 1:
            raise AssessmentServiceError("max_attempts must be at least 1")
        if late_penalty_percent < 0 or late_penalty_percent > 100:
            raise AssessmentServiceError("late_penalty_percent must be between 0 and 100")

        grading_rule = GradingRule(
            grading_rule_id=str(uuid4()),
            tenant_id=tenant_id,
            name=name,
            pass_threshold=pass_threshold,
            negative_marking_ratio=negative_marking_ratio,
            max_attempts=max_attempts,
            allow_partial_credit=allow_partial_credit,
            late_penalty_percent=late_penalty_percent,
            created_by=created_by,
        )
        self.repository.create_grading_rule(grading_rule)
        self._audit("GradingRuleCreated", grading_rule.grading_rule_id, tenant_id, {"name": name})

        return {
            "grading_rule_id": grading_rule.grading_rule_id,
            "name": grading_rule.name,
            "pass_threshold": grading_rule.pass_threshold,
            "audit_event": "GradingRuleCreated",
        }

    def publish_assessment(self, *, tenant_id: str, assessment_id: str, published_by: str) -> Dict:
        assessment = self._get_tenant_assessment(tenant_id=tenant_id, assessment_id=assessment_id)

        if assessment.status == AssessmentStatus.PUBLISHED:
            raise AssessmentPublishValidationError("assessment is already published")

        if not assessment.question_bank_id:
            raise AssessmentPublishValidationError("assessment must reference a question bank before publishing")
        question_bank = self._get_tenant_question_bank(tenant_id=tenant_id, question_bank_id=assessment.question_bank_id)
        if len(question_bank.questions) == 0:
            raise AssessmentPublishValidationError("assessment question bank must contain at least one question")

        if not assessment.grading_rule_id:
            raise AssessmentPublishValidationError("assessment must reference a grading rule before publishing")
        grading_rule = self._get_tenant_grading_rule(tenant_id=tenant_id, grading_rule_id=assessment.grading_rule_id)

        published_at = datetime.utcnow()
        published = replace(
            assessment,
            status=AssessmentStatus.PUBLISHED,
            published_at=published_at,
            updated_at=published_at,
        )
        self.repository.update_assessment(published)
        self._audit(
            "AssessmentPublished",
            assessment_id,
            tenant_id,
            {
                "published_by": published_by,
                "question_count": len(question_bank.questions),
                "pass_threshold": grading_rule.pass_threshold,
            },
        )

        return {
            "assessment_id": assessment_id,
            "status": published.status.value,
            "published_at": published.published_at.isoformat(),
            "published_by": published_by,
            "audit_event": "AssessmentPublished",
        }

    def list_assessments(self, tenant_id: str) -> List[Dict]:
        return [
            {
                "assessment_id": assessment.assessment_id,
                "course_id": assessment.course_id,
                "title": assessment.title,
                "assessment_type": assessment.assessment_type.value,
                "status": assessment.status.value,
            }
            for assessment in self.repository.list_assessments(tenant_id)
        ]

    def _get_tenant_assessment(self, *, tenant_id: str, assessment_id: str) -> Assessment:
        assessment = self.repository.get_assessment(assessment_id)
        if assessment is None:
            raise AssessmentNotFoundError("assessment not found")
        if assessment.tenant_id != tenant_id:
            raise TenantScopeError("cross-tenant assessment access is forbidden")
        return assessment

    def _get_tenant_question_bank(self, *, tenant_id: str, question_bank_id: str) -> QuestionBank:
        question_bank = self.repository.get_question_bank(question_bank_id)
        if question_bank is None:
            raise AssessmentServiceError("question bank not found")
        if question_bank.tenant_id != tenant_id:
            raise TenantScopeError("cross-tenant question bank access is forbidden")
        return question_bank

    def _get_tenant_grading_rule(self, *, tenant_id: str, grading_rule_id: str) -> GradingRule:
        grading_rule = self.repository.get_grading_rule(grading_rule_id)
        if grading_rule is None:
            raise AssessmentServiceError("grading rule not found")
        if grading_rule.tenant_id != tenant_id:
            raise TenantScopeError("cross-tenant grading rule access is forbidden")
        return grading_rule

    def _audit(self, event_type: str, entity_id: str, tenant_id: str, payload: Dict) -> None:
        self.repository.append_event(
            AuditEvent(event_type=event_type, entity_id=entity_id, tenant_id=tenant_id, payload=payload)
        )
