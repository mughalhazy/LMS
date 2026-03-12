# Certificate Service

Tenant-scoped service for certificate lifecycle management.

## Implemented capabilities
- Certificate issuance with support for optional enrollment mapping.
- Certificate validation using certificate id and optional verification code.
- Expiration management with configurable validity windows.
- Certificate storage and retrieval with tenant/user/course/status filters.

## Run tests
```bash
python -m unittest backend/services/certificate-service/tests/test_certificate_service.py
```
