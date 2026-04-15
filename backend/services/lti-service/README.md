# LTI Service

Generated LTI integration service implementing both **LTI provider** and **LTI consumer** responsibilities for LMS external tool interoperability.

## Scope covered
- LTI provider endpoints
- LTI consumer integration
- LTI launch handling
- External tool integration

## API endpoints
### Provider
- `POST /provider/tools/register`
- `POST /provider/tools/validate-activation`
- `POST /provider/launch/login`
- `POST /provider/launch/validate`
- `POST /provider/launch/session`
- `POST /provider/identity/map`
- `POST /provider/identity/normalize-roles`
- `POST /provider/services/token`
- `POST /provider/services/ags/score`
- `POST /provider/services/nrps/sync`

### Consumer
- `POST /consumer/tools/register`
- `POST /consumer/launch/initiate`
- `POST /consumer/launch/complete`

### Utility
- `GET /health`

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
This scaffold follows `/docs/integrations/lti_provider_spec.md`, `/docs/integrations/lti_consumer_spec.md`, and `/docs/integrations/standards_support.md` for LTI 1.3 + Advantage behavior and security controls.
