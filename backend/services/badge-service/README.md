# Badge Service

Badge Service provides learner badge capabilities for LMS certifications.

## Implemented capabilities
- Badge definitions (create, list, update lifecycle metadata)
- Badge issuance (issue, revoke/reactivate controls)
- Learner badge history (timeline-style badge view enriched with badge definitions)

## Run locally
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8091
```

## API endpoints
- `POST /badges`
- `GET /badges`
- `PATCH /badges/{badge_id}`
- `POST /badge-issuances`
- `PATCH /badge-issuances/{issuance_id}`
- `GET /learners/{learner_id}/badges?tenant_id={tenantId}`

## Domain constraints
- Badge code is unique per tenant.
- Badge code is immutable after definition creation.
- Only active badge definitions can be issued.
- Learner can have at most one active issuance per badge.
- Revoked issuances are retained in history and allow re-issuance.
