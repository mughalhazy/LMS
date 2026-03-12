# Assessment Service

This service implements the **assessment_service** bounded context and owns assessment authoring workflows, reusable question banks, grading rule configuration, and assessment publishing.

## Scope implemented

- Assessment creation with tenant-scoped ownership.
- Question bank creation and question item management.
- Grading rules for pass threshold and attempt constraints.
- Publishing workflow with validation gates.

## Responsibilities

- Persist assessment metadata and lifecycle state.
- Persist reusable question banks and question metadata (difficulty/objective tags).
- Persist grading rules and scoring constraints.
- Validate that publish-ready assessments have both question content and grading policy.
- Emit audit events for compliance traceability.

## API handlers

The service exposes framework-adapter friendly handlers in `src/api.py`:

- `create_assessment`
- `create_question_bank`
- `add_question_item`
- `create_grading_rule`
- `publish_assessment`
- `list_assessments`

## Tenant isolation

Every operation requires `tenant_id` and rejects cross-tenant access/mutation.

## Publishing validation rules

`publish_assessment` requires:

1. Assessment is in `draft` state.
2. Assessment references a question bank.
3. Question bank contains at least one question.
4. Assessment references a grading rule.

## Events emitted

- `AssessmentCreated`
- `QuestionBankCreated`
- `QuestionBankItemAdded`
- `GradingRuleCreated`
- `AssessmentPublished`
