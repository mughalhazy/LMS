issue_type
endpoint_or_resource
description
severity
recommended_fix

Missing Core Service API
/auth/* (auth_identity_service)
Service map defines auth_identity_service with UserCredential/AccessToken/Session ownership, but core REST API catalog contains no authentication or token/session endpoints.
high
Add a versioned auth surface (e.g., POST /api/v1/auth/token, POST /api/v1/auth/refresh, POST /api/v1/auth/logout, GET /api/v1/auth/sessions/{sessionId}) and map contracts to auth_identity_service entities.

Missing Core Service API
/organizations, /business-units, /teams, /locations, /learner-groups (organization_catalog_service)
Organization catalog is a core service in architecture but has no API endpoints in the core REST spec, leaving audience targeting and policy scoping without a defined interface.
high
Define organization catalog endpoints under /api/v1/organizations/* with CRUD/read APIs for BusinessUnit, Team, Location, LearnerGroup.

Missing Core Service API
/learning-paths/* (learning_path_service)
LearningPath/PathNode/PrerequisiteRule are listed as core entities in service map but there are no learning path endpoints in the core API.
high
Add learning path APIs (e.g., POST/GET/PATCH /api/v1/learning-paths, /api/v1/learning-paths/{id}/nodes, /api/v1/learning-paths/{id}/prerequisites).

Missing Core Service API
/progress/* (progress_tracking_service)
Progress tracking is defined as a core service with ProgressSnapshot/CompletionRecord entities, but only analytics exposes progress readouts; no operational progress API exists.
medium
Expose operational progress endpoints (e.g., GET /api/v1/progress/learners/{learnerId}, GET /api/v1/progress/courses/{courseId}) and keep analytics endpoints read-optimized/aggregated.

Entity/API Mismatch
/certificates (core REST) vs Certification/Badge/IssuanceRecord (service map)
Service map names the domain as certification_service with Certification + Badge entities, while REST exposes only /certificates and omits badge resources.
medium
Normalize naming and entity coverage by adding /api/v1/certifications and /api/v1/badges (or update service map/entity naming to match certificates-only scope).

API Namespace Inconsistency
Core APIs use unversioned roots (/users, /courses, ...), while integration uses /api/integrations/* and analytics uses /api/v1/analytics/*
API surfaces are separated by function, but inconsistent prefixing/versioning increases routing and lifecycle risk across gateway and contract governance.
medium
Adopt a uniform versioned namespace strategy, e.g., /api/v1/core/*, /api/v1/integrations/*, /api/v1/analytics/* (or /api/v1/{domain}/* consistently).

Analytics Coverage Gap
Analytics model includes cohort and recommendation domains (CohortAssignmentCreated, CohortEngagementMeasured, RecommendationEngaged), but analytics API exposes only learner progress, course performance, skills, and compliance report generation.
medium
Add analytics endpoints for cohort and recommendation outcomes (e.g., GET /api/v1/analytics/cohorts/{cohortId}/engagement, GET /api/v1/analytics/recommendations/performance) or explicitly mark them as internal-only marts.

Integration Contract Clarity
POST /api/integrations/webhooks/events
Integration catalog defines webhook ingestion auth, but does not document event schema/versioning path while architecture mandates schema_registry governance.
low
Publish explicit webhook event contract/versioning rules (e.g., X-Event-Type, X-Schema-Version, JSON schema links) and tie compatibility policy to schema_registry.
