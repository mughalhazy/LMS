import {
  AttachLessonContentInput,
  LearnerContext,
  LessonContentItem,
  LessonResource,
  ReorderLessonContentInput,
  UpsertLessonResourceInput,
  UUID,
  VisibilityRules,
} from "./entities";
import { LessonContentRepository } from "./content.repository";

const DEFAULT_VISIBILITY: VisibilityRules = {
  state: "draft",
  requireEnrollment: true,
};

const makeId = (): UUID =>
  `lc_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;

const nowIso = (): string => new Date().toISOString();

export class LessonContentService {
  constructor(private readonly repository: LessonContentRepository) {}

  async attachContent(input: AttachLessonContentInput): Promise<LessonContentItem> {
    const existing = await this.repository.getContentByLessonId(input.lessonId);
    const orderIndex = input.orderIndex ?? existing.length + 1;

    const item: LessonContentItem = {
      lessonContentId: makeId(),
      lessonId: input.lessonId,
      contentId: input.contentId,
      contentType: input.contentType,
      title: input.title,
      orderIndex,
      visibilityRules: input.visibilityRules ?? DEFAULT_VISIBILITY,
      attachedBy: input.actorUserId,
      attachedAt: nowIso(),
    };

    return this.repository.createContent(item);
  }

  async upsertResource(input: UpsertLessonResourceInput): Promise<LessonResource> {
    const existing = input.resourceId
      ? await this.repository.findResourceById(input.resourceId)
      : null;

    if (existing) {
      const updated: LessonResource = {
        ...existing,
        label: input.label,
        resourceType: input.resourceType,
        uri: input.uri,
        orderIndex: input.orderIndex ?? existing.orderIndex,
        visibilityRules: input.visibilityRules ?? existing.visibilityRules,
      };
      return this.repository.updateResource(updated);
    }

    const lessonResources = await this.repository.getResourcesByLessonId(input.lessonId);
    const resource: LessonResource = {
      resourceId: makeId(),
      lessonId: input.lessonId,
      label: input.label,
      resourceType: input.resourceType,
      uri: input.uri,
      orderIndex: input.orderIndex ?? lessonResources.length + 1,
      visibilityRules: input.visibilityRules,
      createdBy: input.actorUserId,
      createdAt: nowIso(),
    };

    return this.repository.createResource(resource);
  }

  async reorderContent(input: ReorderLessonContentInput): Promise<LessonContentItem[]> {
    const existing = await this.repository.getContentByLessonId(input.lessonId);
    const existingSet = new Set(existing.map((item) => item.lessonContentId));

    for (const lessonContentId of input.orderedLessonContentIds) {
      if (!existingSet.has(lessonContentId)) {
        throw new Error(`Unknown lessonContentId in reorder request: ${lessonContentId}`);
      }
    }

    const updates = input.orderedLessonContentIds.map((lessonContentId, index) => {
      const item = existing.find((entry) => entry.lessonContentId === lessonContentId)!;
      return this.repository.updateContent({
        ...item,
        orderIndex: index + 1,
      });
    });

    return Promise.all(updates);
  }

  async listVisibleLessonContent(
    lessonId: UUID,
    learnerContext: LearnerContext,
  ): Promise<LessonContentItem[]> {
    const items = await this.repository.getContentByLessonId(lessonId);
    return items.filter((item) => this.matchesVisibility(item.visibilityRules, learnerContext));
  }

  private matchesVisibility(rules: VisibilityRules, learnerContext: LearnerContext): boolean {
    if (rules.state !== "published") {
      return false;
    }

    if (rules.requireEnrollment && !learnerContext.isEnrolled) {
      return false;
    }

    const checkAt = learnerContext.currentAt ?? nowIso();
    if (rules.timeWindow?.startsAt && checkAt < rules.timeWindow.startsAt) {
      return false;
    }

    if (rules.timeWindow?.endsAt && checkAt > rules.timeWindow.endsAt) {
      return false;
    }

    if (!rules.audience) {
      return true;
    }

    if (rules.audience.tenantId !== learnerContext.tenantId) {
      return false;
    }

    if (
      rules.audience.organizationIds?.length &&
      learnerContext.organizationId &&
      !rules.audience.organizationIds.includes(learnerContext.organizationId)
    ) {
      return false;
    }

    if (rules.audience.cohortIds?.length) {
      const cohorts = new Set(learnerContext.cohortIds ?? []);
      const overlap = rules.audience.cohortIds.some((cohortId) => cohorts.has(cohortId));
      if (!overlap) {
        return false;
      }
    }

    if (rules.audience.roleIds?.length) {
      const roles = new Set(learnerContext.roleIds ?? []);
      const overlap = rules.audience.roleIds.some((roleId) => roles.has(roleId));
      if (!overlap) {
        return false;
      }
    }

    return true;
  }
}
