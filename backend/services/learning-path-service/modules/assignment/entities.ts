export type AssignmentTargetType = "user" | "group" | "department";

export type AssignmentStatus = "active" | "revoked";

export interface LearningPathAssignment {
  assignmentId: string;
  tenantId: string;
  pathId: string;
  targetType: AssignmentTargetType;
  targetId: string;
  effectiveFrom: string;
  effectiveTo?: string;
  status: AssignmentStatus;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
}

export interface AssignLearningPathRequest {
  tenantId: string;
  pathId: string;
  targetType: AssignmentTargetType;
  targetId: string;
  effectiveFrom?: string;
  effectiveTo?: string;
  createdBy: string;
}

export interface AssignmentFilters {
  tenantId: string;
  pathId?: string;
  targetType?: AssignmentTargetType;
  targetId?: string;
  status?: AssignmentStatus;
}

export interface AssignmentAudienceSummary {
  tenantId: string;
  pathId: string;
  directUsers: string[];
  groups: string[];
  departments: string[];
}
