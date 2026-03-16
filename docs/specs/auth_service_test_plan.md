# Auth Service Test Plan

## Test suites

1. `spec/requests/auth/login_spec.rb`
   - valid password login
   - invalid credential rejection
   - tenant mismatch rejection
   - throttling response

2. `spec/requests/auth/token_spec.rb`
   - refresh token rotation success
   - replayed refresh token triggers chain revocation
   - token validation success/failure

3. `spec/requests/auth/password_reset_spec.rb`
   - forgot password returns 202 for existing/non-existing user
   - reset challenge expiry failure
   - successful reset revokes active sessions

4. `spec/domain/session_lifecycle_spec.rb`
   - session state machine (`active -> revoked/expired`)
   - revoke-all by tenant/user

5. `spec/contract/user_service_client_spec.rb`
   - compatibility with user-service identity lookup contract
   - lock/suspend/terminated user behavior

6. `spec/integration/event_publishing_spec.rb`
   - required auth lifecycle events emitted with envelope fields
   - outbox retry idempotency by `event_id`

## Security test cases

- JWT signature tampering and `alg` confusion rejection.
- Expired/nbf-invalid token rejection.
- Cross-tenant token misuse detection.
- Password reset brute-force lockout.
- PII redaction verification in logs.

## Performance and resilience checks

- p95 `/login` < 300ms at target concurrency.
- p95 `/token` refresh < 200ms.
- Event bus outage: outbox buffering without request failure.
