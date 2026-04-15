# Learning Path Assignment Module

Implements tenant-scoped assignment of learning paths to:

- individual users
- groups
- departments

## Entities used

- `LearningPathAssignment`
- `AssignLearningPathRequest`
- `AssignmentAudienceSummary`

## API endpoints

- `POST /tenants/{tenantId}/learning-paths/{pathId}/assignments`
- `POST /tenants/{tenantId}/learning-paths/assignments/{assignmentId}/revoke`
- `GET /tenants/{tenantId}/learning-paths/{pathId}/audience`

## Tenant scope guardrails

All repository queries and mutation operations require `tenantId` and enforce matching target membership via tenant-aware directories (`UserDirectory`, `GroupDirectory`, `DepartmentDirectory`).
