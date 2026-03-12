# Tenant Service

Implements tenant lifecycle, tenant configuration, and tenant isolation enforcement for LMS.

## Entities
- `Tenant`
- `TenantConfiguration`
- `TenantNamespace`
- `LifecycleEvent`

## API Endpoints (service methods)
- `validate_tenant_creation`
- `create_tenant`
- `initialize_tenant_configuration`
- `update_tenant_configuration`
- `get_tenant_configuration`
- `manage_tenant_feature_flags`
- `suspend_tenant`
- `reactivate_tenant`
- `archive_tenant`
- `decommission_tenant`
- `get_tenant_lifecycle_status`
- `evaluate_isolation`
