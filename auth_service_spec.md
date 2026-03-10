endpoint | method | purpose
--- | --- | ---
`/api/v1/auth/login` | `POST` | Authenticates user credentials (or SSO assertion exchange) and starts an authenticated session context.
`/api/v1/auth/token` | `POST` | Generates access and refresh tokens for authenticated clients with scoped claims and expiry.
`/api/v1/auth/sessions/validate` | `POST` | Validates active session/token state (signature, expiry, revocation, tenant context) before protected API access.
`/api/v1/auth/password/forgot` | `POST` | Initiates password reset by issuing a one-time reset challenge to a verified recovery channel.
`/api/v1/auth/password/reset` | `POST` | Completes password reset using a valid reset challenge and sets a new password under policy rules.
