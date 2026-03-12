from __future__ import annotations

from typing import Dict, List, Optional

from .models import Assessment, AuditEvent, GradingRule, QuestionBank


class InMemoryAssessmentRepository:
    def __init__(self) -> None:
        self.assessments: Dict[str, Assessment] = {}
        self.question_banks: Dict[str, QuestionBank] = {}
        self.grading_rules: Dict[str, GradingRule] = {}
        self.events: List[AuditEvent] = []

    def create_assessment(self, assessment: Assessment) -> None:
        self.assessments[assessment.assessment_id] = assessment

    def update_assessment(self, assessment: Assessment) -> None:
        self.assessments[assessment.assessment_id] = assessment

    def get_assessment(self, assessment_id: str) -> Optional[Assessment]:
        return self.assessments.get(assessment_id)

    def list_assessments(self, tenant_id: str) -> List[Assessment]:
        return [a for a in self.assessments.values() if a.tenant_id == tenant_id]

    def create_question_bank(self, question_bank: QuestionBank) -> None:
        self.question_banks[question_bank.question_bank_id] = question_bank

    def update_question_bank(self, question_bank: QuestionBank) -> None:
        self.question_banks[question_bank.question_bank_id] = question_bank

    def get_question_bank(self, question_bank_id: str) -> Optional[QuestionBank]:
        return self.question_banks.get(question_bank_id)

    def create_grading_rule(self, grading_rule: GradingRule) -> None:
        self.grading_rules[grading_rule.grading_rule_id] = grading_rule

    def get_grading_rule(self, grading_rule_id: str) -> Optional[GradingRule]:
        return self.grading_rules.get(grading_rule_id)

    def append_event(self, event: AuditEvent) -> None:
        self.events.append(event)
