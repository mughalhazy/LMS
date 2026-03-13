# Centralized Secrets Management

This directory configures LMS centralized secrets management for all services in `backend/services`.

## What is configured

- **Secret storage** via Vault paths in `secrets-catalog.yaml`.
- **Environment variable injection** via External Secrets + Kubernetes deployment template in `env-injection-template.yaml`.
- **API key storage** under `secret/data/lms/services/<service>/api#api_key`.
- **Database credential management** under `secret/data/lms/services/<service>/database#url`.
- **Encryption key storage** under `secret/data/lms/services/<service>/crypto#encryption_key`.

## Service coverage

`service-secret-mapping.json` includes a mapping for every service discovered under `backend/services`.

## Verification

Run:

```bash
python infrastructure/secrets-management/verify_secrets_management.py
```

Verification checks:

1. No obvious hardcoded secrets in service source files.
2. Every service has a secrets-manager mapping.
3. A report is generated at `verification-report.json` with:
   - `secrets_configured`
   - `services_using_secrets`
   - `security_status`
