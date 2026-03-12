import {
  EnrollmentDecision,
  LearnerTranscriptRecord,
  LearningPathDefinition,
  PrerequisiteRuleDefinition,
  TenantRulePolicy,
  UUID
} from "../domain/entities.js";

export interface PrerequisiteRepository {
  saveRule(rule: PrerequisiteRuleDefinition): void;
  getRuleByCourse(tenantId: UUID, courseId: UUID): PrerequisiteRuleDefinition | undefined;
}

export interface LearningPathRepository {
  savePath(path: LearningPathDefinition): void;
  getPath(tenantId: UUID, pathId: UUID): LearningPathDefinition | undefined;
}

export interface TranscriptRepository {
  getLearnerTranscript(tenantId: UUID, userId: UUID): LearnerTranscriptRecord[];
  seed(records: LearnerTranscriptRecord[]): void;
}

export interface TenantPolicyRepository {
  getPolicy(tenantId: UUID): TenantRulePolicy;
  upsertPolicy(policy: TenantRulePolicy): void;
}

export class PrerequisiteEngineService {
  constructor(
    private readonly prerequisiteRepo: PrerequisiteRepository,
    private readonly transcriptRepo: TranscriptRepository,
    private readonly learningPathRepo: LearningPathRepository,
    private readonly tenantPolicyRepo: TenantPolicyRepository
  ) {}

  definePrerequisiteRule(rule: PrerequisiteRuleDefinition): PrerequisiteRuleDefinition {
    this.validatePrerequisiteDefinition(rule);
    this.prerequisiteRepo.saveRule(rule);
    return rule;
  }

  validatePrerequisiteDefinition(rule: PrerequisiteRuleDefinition): void {
    if (rule.prerequisiteNodes.length === 0) {
      throw new Error("Prerequisite definition requires at least one prerequisite node.");
    }

    const seen = new Set<string>();
    for (const node of rule.prerequisiteNodes) {
      if (node.requiredCourseId === rule.courseId) {
        throw new Error("Course cannot require itself as a prerequisite.");
      }
      if (seen.has(node.id)) {
        throw new Error(`Duplicate prerequisite node id: ${node.id}`);
      }
      seen.add(node.id);
    }
  }

  checkCourseEligibility(input: { tenantId: UUID; userId: UUID; courseId: UUID }): EnrollmentDecision {
    const rule = this.prerequisiteRepo.getRuleByCourse(input.tenantId, input.courseId);
    if (!rule) {
      return {
        ...input,
        decision: "APPROVED",
        unmetPrerequisiteNodeIds: [],
        recommendationCourseIds: [],
        evaluatedAt: new Date().toISOString()
      };
    }

    const policy = this.tenantPolicyRepo.getPolicy(input.tenantId);
    const transcript = this.transcriptRepo.getLearnerTranscript(input.tenantId, input.userId);

    const unmet = rule.prerequisiteNodes.filter((node) => {
      const equivalentCourseIds = rule.equivalencyCourseIds?.[node.requiredCourseId] ?? [];
      const acceptableCourseIds = [node.requiredCourseId, ...equivalentCourseIds];

      const matching = transcript.find((record) => {
        if (!acceptableCourseIds.includes(record.courseId)) {
          return false;
        }
        if (!policy.acceptedCompletionStates.includes(record.completionState)) {
          return false;
        }
        if (node.minimumGrade !== undefined && (record.grade ?? 0) < node.minimumGrade) {
          return false;
        }
        if (node.validityWindowDays && record.completedAt) {
          const completedAt = new Date(record.completedAt).getTime();
          const ageMs = Date.now() - completedAt;
          return ageMs > node.validityWindowDays * 24 * 60 * 60 * 1000 ? false : true;
        }
        return true;
      });

      return !matching;
    });

    const unmetIds = unmet.map((u) => u.id);
    const passes = rule.mode === "ALL" ? unmetIds.length === 0 : unmetIds.length < rule.prerequisiteNodes.length;

    return {
      ...input,
      decision: passes ? "APPROVED" : "BLOCKED",
      unmetPrerequisiteNodeIds: unmetIds,
      recommendationCourseIds: unmet.map((u) => u.requiredCourseId),
      evaluatedAt: new Date().toISOString()
    };
  }

  validateLearningPathDependencies(path: LearningPathDefinition): { valid: boolean; errors: string[] } {
    const adjacency = new Map<string, string[]>();
    const errors: string[] = [];

    for (const dep of path.dependencies) {
      if (!adjacency.has(dep.fromNodeId)) {
        adjacency.set(dep.fromNodeId, []);
      }
      adjacency.get(dep.fromNodeId)?.push(dep.toNodeId);

      if (dep.type === "SCORE_THRESHOLD" && dep.minimumScore === undefined) {
        errors.push(`Dependency ${dep.id} is SCORE_THRESHOLD but minimumScore is missing.`);
      }
    }

    const visiting = new Set<string>();
    const visited = new Set<string>();
    const hasCycle = (node: string): boolean => {
      if (visiting.has(node)) return true;
      if (visited.has(node)) return false;

      visiting.add(node);
      for (const neighbor of adjacency.get(node) ?? []) {
        if (hasCycle(neighbor)) return true;
      }
      visiting.delete(node);
      visited.add(node);
      return false;
    };

    for (const node of adjacency.keys()) {
      if (hasCycle(node)) {
        errors.push(`Cycle detected in learning path ${path.pathId}.`);
        break;
      }
    }

    if (errors.length === 0) {
      this.learningPathRepo.savePath(path);
    }

    return { valid: errors.length === 0, errors };
  }

  upsertTenantPolicy(policy: TenantRulePolicy): TenantRulePolicy {
    this.tenantPolicyRepo.upsertPolicy(policy);
    return policy;
  }
}
