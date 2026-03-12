import {
  LearnerTranscriptRecord,
  LearningPathDefinition,
  PrerequisiteRuleDefinition,
  TenantRulePolicy,
  UUID
} from "../domain/entities.js";
import {
  LearningPathRepository,
  PrerequisiteRepository,
  TenantPolicyRepository,
  TranscriptRepository
} from "../application/prerequisite-engine.js";

export class InMemoryPrerequisiteRepository implements PrerequisiteRepository {
  private readonly byTenantCourse = new Map<string, PrerequisiteRuleDefinition>();

  saveRule(rule: PrerequisiteRuleDefinition): void {
    this.byTenantCourse.set(`${rule.tenantId}:${rule.courseId}`, rule);
  }

  getRuleByCourse(tenantId: UUID, courseId: UUID): PrerequisiteRuleDefinition | undefined {
    return this.byTenantCourse.get(`${tenantId}:${courseId}`);
  }
}

export class InMemoryLearningPathRepository implements LearningPathRepository {
  private readonly byTenantPath = new Map<string, LearningPathDefinition>();

  savePath(path: LearningPathDefinition): void {
    this.byTenantPath.set(`${path.tenantId}:${path.pathId}`, path);
  }

  getPath(tenantId: UUID, pathId: UUID): LearningPathDefinition | undefined {
    return this.byTenantPath.get(`${tenantId}:${pathId}`);
  }
}

export class InMemoryTranscriptRepository implements TranscriptRepository {
  private readonly transcript: LearnerTranscriptRecord[] = [];

  getLearnerTranscript(tenantId: UUID, userId: UUID): LearnerTranscriptRecord[] {
    return this.transcript.filter((record) => record.tenantId === tenantId && record.userId === userId);
  }

  seed(records: LearnerTranscriptRecord[]): void {
    this.transcript.push(...records);
  }
}

export class InMemoryTenantPolicyRepository implements TenantPolicyRepository {
  private readonly policies = new Map<UUID, TenantRulePolicy>();

  getPolicy(tenantId: UUID): TenantRulePolicy {
    return (
      this.policies.get(tenantId) ?? {
        tenantId,
        allowAdvisoryBypass: true,
        acceptedCompletionStates: ["COMPLETED"]
      }
    );
  }

  upsertPolicy(policy: TenantRulePolicy): void {
    this.policies.set(policy.tenantId, policy);
  }
}
