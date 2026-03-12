# RBAC Authorization Service

Implements LMS RBAC primitives from `docs/specs/rbac_spec.md`:
- roles
- permissions
- role assignments
- authorization middleware

## Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

## API Endpoints

- `GET /health`
- `GET /roles`
- `GET /permissions`
- `GET /assignments`
- `POST /assignments`
- `POST /authorize`
- `GET /audit-log` (protected by middleware requiring `audit.view_tenant`)

## Authorization Middleware

Use these headers with protected routes:
- `X-Principal-Id`
- `X-Principal-Type`
- `X-Scope-Type`
- `X-Scope-Id`
- `X-Correlation-Id` (optional)
