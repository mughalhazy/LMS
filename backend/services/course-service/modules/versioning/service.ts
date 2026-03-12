import {
  CourseVersion,
  CourseVersionPointer,
  CreateVersionInput,
  PublishVersionInput,
  RollbackVersionInput,
  VersionAuditEvent,
  VersionHistoryQuery,
} from "./types";
import { CourseVersionRepository } from "./repository";

export class CourseVersioningService {
  constructor(private readonly repository: CourseVersionRepository) {}

  async createVersion(input: CreateVersionInput): Promise<CourseVersion> {
    const now = this.now();
    const versions = await this.repository.getVersions(input.tenantId, input.courseId);
    const nextVersionNumber = (versions[0]?.versionNumber ?? 0) + 1;

    const version: CourseVersion = {
      versionId: this.id("ver"),
      tenantId: input.tenantId,
      courseId: input.courseId,
      versionNumber: nextVersionNumber,
      state: "draft",
      contentPayload: input.contentPayload,
      diffFromPrevious: this.calculateDiff(versions[0]?.contentPayload, input.contentPayload),
      changeSummary: input.changeSummary,
      createdBy: input.editorId,
      createdAt: now,
      metadata: {
        ...(versions[0]?.metadata ?? {}),
        ...(input.metadataUpdates ?? {}),
      },
    };

    if (input.sourceVersion !== undefined) {
      const source = await this.repository.getVersion(input.tenantId, input.courseId, input.sourceVersion);
      if (!source) {
        throw new Error(`sourceVersion ${input.sourceVersion} not found`);
      }
      version.diffFromPrevious = this.calculateDiff(source.contentPayload, input.contentPayload);
    }

    await this.supersedeActiveDraft(input.tenantId, input.courseId, input.editorId);
    await this.repository.saveVersion(version);

    await this.savePointer({
      tenantId: input.tenantId,
      courseId: input.courseId,
      draftVersionNumber: version.versionNumber,
      publishedVersionNumber: (await this.repository.getPointer(input.tenantId, input.courseId))?.publishedVersionNumber,
      updatedAt: now,
    });

    await this.audit({
      tenantId: input.tenantId,
      courseId: input.courseId,
      versionNumber: version.versionNumber,
      action: "created",
      actorId: input.editorId,
      details: {
        changeSummary: input.changeSummary,
      },
    });

    return version;
  }

  async getVersionHistory(query: VersionHistoryQuery): Promise<{ versions: CourseVersion[]; total: number; pointer?: CourseVersionPointer }> {
    const allVersions = await this.repository.getVersions(query.tenantId, query.courseId);
    const offset = query.offset ?? 0;
    const limit = query.limit ?? 50;
    return {
      versions: allVersions.slice(offset, offset + limit),
      total: allVersions.length,
      pointer: await this.repository.getPointer(query.tenantId, query.courseId),
    };
  }

  async rollbackVersion(input: RollbackVersionInput): Promise<CourseVersion> {
    const target = await this.repository.getVersion(input.tenantId, input.courseId, input.targetVersionNumber);
    if (!target) {
      throw new Error(`targetVersionNumber ${input.targetVersionNumber} not found`);
    }

    const rollbackDraft = await this.createVersion({
      tenantId: input.tenantId,
      courseId: input.courseId,
      sourceVersion: input.targetVersionNumber,
      changeSummary: `Rollback to v${input.targetVersionNumber}: ${input.rollbackReason}`,
      editorId: input.requestedBy,
      contentPayload: target.contentPayload,
      metadataUpdates: {
        rollbackReason: input.rollbackReason,
      },
    });

    rollbackDraft.rollbackOriginVersion = input.targetVersionNumber;
    await this.repository.updateVersion(rollbackDraft);

    await this.audit({
      tenantId: input.tenantId,
      courseId: input.courseId,
      versionNumber: rollbackDraft.versionNumber,
      action: "rollback",
      actorId: input.requestedBy,
      reason: input.rollbackReason,
      details: {
        rollbackOriginVersion: input.targetVersionNumber,
      },
    });

    return rollbackDraft;
  }

  async publishVersion(input: PublishVersionInput): Promise<CourseVersion> {
    const version = await this.repository.getVersion(input.tenantId, input.courseId, input.versionNumber);
    if (!version) {
      throw new Error(`Version ${input.versionNumber} not found`);
    }

    if (version.state === "published") {
      return version;
    }

    const now = this.now();
    version.state = "published";
    version.publishedBy = input.publisherId;
    version.publishedAt = now;
    version.releaseNotes = input.releaseNotes;
    await this.repository.updateVersion(version);

    const pointer = await this.repository.getPointer(input.tenantId, input.courseId);
    await this.savePointer({
      tenantId: input.tenantId,
      courseId: input.courseId,
      draftVersionNumber: pointer?.draftVersionNumber === version.versionNumber ? undefined : pointer?.draftVersionNumber,
      publishedVersionNumber: version.versionNumber,
      updatedAt: now,
    });

    await this.audit({
      tenantId: input.tenantId,
      courseId: input.courseId,
      versionNumber: version.versionNumber,
      action: "published",
      actorId: input.publisherId,
      details: {
        releaseNotes: input.releaseNotes,
      },
    });

    return version;
  }

  private async supersedeActiveDraft(tenantId: string, courseId: string, actorId: string): Promise<void> {
    const pointer = await this.repository.getPointer(tenantId, courseId);
    if (!pointer?.draftVersionNumber) {
      return;
    }

    const activeDraft = await this.repository.getVersion(tenantId, courseId, pointer.draftVersionNumber);
    if (!activeDraft || activeDraft.state !== "draft") {
      return;
    }

    activeDraft.state = "superseded";
    await this.repository.updateVersion(activeDraft);
    await this.audit({
      tenantId,
      courseId,
      versionNumber: activeDraft.versionNumber,
      action: "superseded",
      actorId,
      details: {
        reason: "new_draft_created",
      },
    });
  }

  private async savePointer(pointer: CourseVersionPointer): Promise<void> {
    await this.repository.savePointer(pointer);
  }

  private async audit(event: Omit<VersionAuditEvent, "eventId" | "occurredAt">): Promise<void> {
    await this.repository.appendAuditEvent({
      ...event,
      eventId: this.id("audit"),
      occurredAt: this.now(),
    });
  }

  private calculateDiff(
    fromPayload: Record<string, unknown> | undefined,
    toPayload: Record<string, unknown>,
  ): Record<string, unknown> | undefined {
    if (!fromPayload) {
      return undefined;
    }

    const changedEntries = Object.entries(toPayload).filter(([key, value]) => fromPayload[key] !== value);
    return changedEntries.reduce<Record<string, unknown>>((acc, [key, value]) => {
      acc[key] = {
        before: fromPayload[key],
        after: value,
      };
      return acc;
    }, {});
  }

  private id(prefix: string): string {
    return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
  }

  private now(): string {
    return new Date().toISOString();
  }
}
