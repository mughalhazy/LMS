import {
  AssignLearningPathRequest,
  AssignmentAudienceSummary,
  AssignmentTargetType,
  LearningPathAssignment,
} from "./entities";
import { LearningPathAssignmentRepository } from "./repository";

interface GroupDirectory {
  exists(tenantId: string, groupId: string): Promise<boolean>;
  listUsers(tenantId: string, groupId: string): Promise<string[]>;
}

interface DepartmentDirectory {
  exists(tenantId: string, departmentId: string): Promise<boolean>;
  listUsers(tenantId: string, departmentId: string): Promise<string[]>;
}

interface UserDirectory {
  exists(tenantId: string, userId: string): Promise<boolean>;
}

const SUPPORTED_TARGETS: AssignmentTargetType[] = [
  "user",
  "group",
  "department",
];

export class LearningPathAssignmentService {
  constructor(
    private readonly repository: LearningPathAssignmentRepository,
    private readonly userDirectory: UserDirectory,
    private readonly groupDirectory: GroupDirectory,
    private readonly departmentDirectory: DepartmentDirectory,
  ) {}

  async assign(request: AssignLearningPathRequest): Promise<LearningPathAssignment> {
    this.validateRequest(request);
    await this.ensureTargetExists(request);

    const now = new Date().toISOString();
    const assignment: LearningPathAssignment = {
      assignmentId: this.buildAssignmentId(),
      tenantId: request.tenantId,
      pathId: request.pathId,
      targetType: request.targetType,
      targetId: request.targetId,
      effectiveFrom: request.effectiveFrom ?? now,
      effectiveTo: request.effectiveTo,
      status: "active",
      createdBy: request.createdBy,
      createdAt: now,
      updatedAt: now,
    };

    return this.repository.create(assignment);
  }

  async revoke(
    tenantId: string,
    assignmentId: string,
    updatedBy: string,
  ): Promise<LearningPathAssignment> {
    void updatedBy;
    const assignment = await this.repository.findById(tenantId, assignmentId);
    if (!assignment) {
      throw new Error("assignment_not_found");
    }

    const updated: LearningPathAssignment = {
      ...assignment,
      status: "revoked",
      updatedAt: new Date().toISOString(),
    };

    return this.repository.update(updated);
  }

  async getAudienceSummary(
    tenantId: string,
    pathId: string,
  ): Promise<AssignmentAudienceSummary> {
    const activeAssignments = await this.repository.findMany({
      tenantId,
      pathId,
      status: "active",
    });

    const directUsers = new Set<string>();
    const groups = new Set<string>();
    const departments = new Set<string>();

    for (const assignment of activeAssignments) {
      if (assignment.targetType === "user") {
        directUsers.add(assignment.targetId);
        continue;
      }

      if (assignment.targetType === "group") {
        groups.add(assignment.targetId);
        const groupUsers = await this.groupDirectory.listUsers(
          tenantId,
          assignment.targetId,
        );
        groupUsers.forEach((userId) => directUsers.add(userId));
        continue;
      }

      departments.add(assignment.targetId);
      const departmentUsers = await this.departmentDirectory.listUsers(
        tenantId,
        assignment.targetId,
      );
      departmentUsers.forEach((userId) => directUsers.add(userId));
    }

    return {
      tenantId,
      pathId,
      directUsers: Array.from(directUsers.values()),
      groups: Array.from(groups.values()),
      departments: Array.from(departments.values()),
    };
  }

  private validateRequest(request: AssignLearningPathRequest): void {
    if (!request.tenantId || !request.pathId || !request.targetId || !request.createdBy) {
      throw new Error("invalid_assignment_request");
    }

    if (!SUPPORTED_TARGETS.includes(request.targetType)) {
      throw new Error("unsupported_assignment_target_type");
    }

    if (request.effectiveFrom && request.effectiveTo) {
      const from = Date.parse(request.effectiveFrom);
      const to = Date.parse(request.effectiveTo);
      if (Number.isNaN(from) || Number.isNaN(to) || to < from) {
        throw new Error("invalid_effective_window");
      }
    }
  }

  private async ensureTargetExists(request: AssignLearningPathRequest): Promise<void> {
    const { tenantId, targetType, targetId } = request;

    if (targetType === "user") {
      const exists = await this.userDirectory.exists(tenantId, targetId);
      if (!exists) {
        throw new Error("target_user_not_found_in_tenant");
      }
      return;
    }

    if (targetType === "group") {
      const exists = await this.groupDirectory.exists(tenantId, targetId);
      if (!exists) {
        throw new Error("target_group_not_found_in_tenant");
      }
      return;
    }

    const exists = await this.departmentDirectory.exists(tenantId, targetId);
    if (!exists) {
      throw new Error("target_department_not_found_in_tenant");
    }
  }

  private buildAssignmentId(): string {
    return `lpa_${Date.now()}_${Math.random().toString(36).slice(2, 10)}`;
  }
}
