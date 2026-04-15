import { StorageModuleConfig } from "./config";
import { AccessRequest } from "./types";

export class SecureAccessService {
  constructor(private readonly config: StorageModuleConfig) {}

  authorize(request: AccessRequest): void {
    this.enforceTenantBoundary(request);

    const allowedRoles = new Set(["admin", "instructor", "learner", "content_manager"]);
    const hasAllowedRole = request.roles.some((role) => allowedRoles.has(role));

    if (!hasAllowedRole) {
      throw new Error(`Access denied for requester ${request.requesterId}: role is not authorized`);
    }

    if (request.contentType === "scorm_package" && !request.roles.includes("learner") && !request.roles.includes("instructor") && !request.roles.includes("admin")) {
      throw new Error(`Access denied for requester ${request.requesterId}: SCORM launch permission missing`);
    }
  }

  private enforceTenantBoundary(request: AccessRequest): void {
    if (!this.config.enforceTenantPrefixIsolation) {
      return;
    }

    const tenantPrefix = `tenants/${request.tenantId}/`;
    if (!request.objectKey.startsWith(tenantPrefix)) {
      throw new Error(
        `Tenant isolation violation. Expected object key prefix '${tenantPrefix}' for tenant ${request.tenantId}`,
      );
    }
  }
}
