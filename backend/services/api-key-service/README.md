# API Key Service

Service responsible for machine-to-machine API credentials used by integration clients.

## Capabilities
- API key creation with integration scopes.
- API key rotation that revokes the previous key.
- Scope-based authorization checks for integration endpoints.
- Usage tracking per key and per scope.

## Endpoints
- `POST /api/v1/integrations/api-keys`
- `POST /api/v1/integrations/api-keys/rotate`
- `POST /api/v1/integrations/api-keys/authorize`
- `POST /api/v1/integrations/api-keys/usage`

## Run
```bash
python -m app.main
```

## Test
```bash
PYTHONPATH=. pytest -q
```
