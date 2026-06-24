# LTI Service

Generated LTI integration service implementing both **LTI provider** and **LTI consumer** responsibilities for LMS external tool interoperability.

## Scope covered
- LTI provider endpoints
- LTI consumer integration
- LTI launch handling
- External tool integration

## API endpoints
### Provider
- `POST /api/v1/lti/provider/tools/register`
- `POST /api/v1/lti/provider/tools/validate-activation`
- `POST /api/v1/lti/provider/launch/login`
- `POST /api/v1/lti/provider/launch/validate`
- `POST /api/v1/lti/provider/launch/session`
- `POST /api/v1/lti/provider/identity/map`
- `POST /api/v1/lti/provider/identity/normalize-roles`
- `POST /api/v1/lti/provider/services/token`
- `POST /api/v1/lti/provider/services/ags/score`
- `POST /api/v1/lti/provider/services/nrps/sync`

### Consumer
- `POST /api/v1/lti/consumer/tools/register`
- `POST /api/v1/lti/consumer/launch/initiate`
- `POST /api/v1/lti/consumer/launch/complete`

### Utility
- `GET /health`
- `GET /metrics`

## LTI flows modeled
1. **Provider registration and activation** (tool onboarding + trust policy checks).
2. **Provider launch** (OIDC login initiation -> id_token validation -> session provisioning).
3. **Provider service access** (AGS/NRPS token issuance + grade passback + membership sync).
4. **Consumer external tool launch** (platform registration -> launch initiate -> launch complete).

## Run
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8090
```

## Notes
This scaffold follows `/docs/integrations/lti-provider-spec.md`, `/docs/integrations/lti-consumer-spec.md`, and `/docs/integrations/standards-support.md` for LTI 1.3 + Advantage behavior and security controls.
