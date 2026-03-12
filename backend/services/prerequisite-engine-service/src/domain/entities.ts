export type UUID = string;

export type RuleMode = "ALL" | "ANY";
export type DependencyType = "SEQUENTIAL_UNLOCK" | "MILESTONE_GATE" | "CO_REQUISITE" | "SCORE_THRESHOLD";

export interface PrerequisiteNode {
  id: UUID;
  requiredCourseId: UUID;
  minimumGrade?: number;
  validityWindowDays?: number;
}

export interface PrerequisiteRuleDefinition {
  id: UUID;
  tenantId: UUID;
  courseId: UUID;
  mode: RuleMode;
  prerequisiteNodes: PrerequisiteNode[];
  equivalencyCourseIds?: Record<UUID, UUID[]>;
  createdBy: UUID;
  createdAt: string;
}

export interface LearningPathDependency {
  id: UUID;
  fromNodeId: UUID;
  toNodeId: UUID;
  strict: boolean;
  type: DependencyType;
  minimumScore?: number;
}

export interface LearningPathDefinition {
  id: UUID;
  tenantId: UUID;
  pathId: UUID;
  dependencies: LearningPathDependency[];
  policyVersion: string;
}

export interface LearnerTranscriptRecord {
  userId: UUID;
  tenantId: UUID;
  courseId: UUID;
  completionState: "COMPLETED" | "IN_PROGRESS" | "NOT_STARTED";
  grade?: number;
  completedAt?: string;
}

export interface EnrollmentDecision {
  tenantId: UUID;
  userId: UUID;
  courseId: UUID;
  decision: "APPROVED" | "BLOCKED";
  unmetPrerequisiteNodeIds: UUID[];
  recommendationCourseIds: UUID[];
  evaluatedAt: string;
}

export interface TenantRulePolicy {
  tenantId: UUID;
  allowAdvisoryBypass: boolean;
  acceptedCompletionStates: LearnerTranscriptRecord["completionState"][];
}
