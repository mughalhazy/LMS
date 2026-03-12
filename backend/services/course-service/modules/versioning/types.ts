export type VersionState = "draft" | "published" | "superseded";

export interface CourseVersion {
  versionId: string;
  tenantId: string;
  courseId: string;
  versionNumber: number;
  state: VersionState;
  contentPayload: Record<string, unknown>;
  diffFromPrevious?: Record<string, unknown>;
  changeSummary: string;
  createdBy: string;
  createdAt: string;
  publishedBy?: string;
  publishedAt?: string;
  releaseNotes?: string;
  rollbackOriginVersion?: number;
  metadata: Record<string, unknown>;
}

export interface CourseVersionPointer {
  tenantId: string;
  courseId: string;
  draftVersionNumber?: number;
  publishedVersionNumber?: number;
  updatedAt: string;
}

export interface VersionAuditEvent {
  eventId: string;
  tenantId: string;
  courseId: string;
  versionNumber: number;
  action: "created" | "published" | "rollback" | "superseded";
  actorId: string;
  reason?: string;
  occurredAt: string;
  details?: Record<string, unknown>;
}

export interface CreateVersionInput {
  tenantId: string;
  courseId: string;
  sourceVersion?: number;
  changeSummary: string;
  editorId: string;
  contentPayload: Record<string, unknown>;
  metadataUpdates?: Record<string, unknown>;
}

export interface RollbackVersionInput {
  tenantId: string;
  courseId: string;
  targetVersionNumber: number;
  rollbackReason: string;
  requestedBy: string;
}

export interface PublishVersionInput {
  tenantId: string;
  courseId: string;
  versionNumber: number;
  publisherId: string;
  releaseNotes?: string;
}

export interface VersionHistoryQuery {
  tenantId: string;
  courseId: string;
  limit?: number;
  offset?: number;
}
