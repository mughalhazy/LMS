# Prerequisite Engine Service

Tenant-scoped microservice for prerequisite definition, validation, course eligibility checks, and learning-path dependency validation.

## Responsibilities
- Manage prerequisite definitions per tenant/course.
- Validate prerequisite rule integrity.
- Evaluate learner eligibility using transcript completion, grade thresholds, validity windows, and equivalency mapping.
- Validate learning-path dependencies (including acyclicity checks).
- Enforce tenant-specific acceptance policies.

## API Endpoints
Base path: `/api/v1/prerequisite-engine`

- `POST /tenant-policies`
- `POST /prerequisite-rules`
- `POST /eligibility/check`
- `POST /learning-paths/validate`

## Run
```bash
npm install
npm run dev
```

## Build
```bash
npm run build
npm start
```
