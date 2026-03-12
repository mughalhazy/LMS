export type UUID = string;

export type ContentType =
  | "video"
  | "audio"
  | "document"
  | "scorm_package"
  | "assessment_asset";

export type ResourceType = "link" | "file" | "reference";

export type LessonVisibility = "draft" | "published";

export interface TimeWindow {
  startsAt?: string;
  endsAt?: string;
}

export interface AudienceScope {
  tenantId: UUID;
  organizationIds?: UUID[];
  cohortIds?: UUID[];
  roleIds?: string[];
}

export interface VisibilityRules {
  state: LessonVisibility;
  timeWindow?: TimeWindow;
  audience?: AudienceScope;
  requireEnrollment?: boolean;
}

export interface LessonContentItem {
  lessonContentId: UUID;
  lessonId: UUID;
  contentId: UUID;
  contentType: ContentType;
  title: string;
  orderIndex: number;
  visibilityRules: VisibilityRules;
  attachedBy: UUID;
  attachedAt: string;
}

export interface LessonResource {
  resourceId: UUID;
  lessonId: UUID;
  label: string;
  resourceType: ResourceType;
  uri: string;
  orderIndex: number;
  visibilityRules?: VisibilityRules;
  createdBy: UUID;
  createdAt: string;
}

export interface AttachLessonContentInput {
  lessonId: UUID;
  contentId: UUID;
  contentType: ContentType;
  title: string;
  orderIndex?: number;
  visibilityRules?: VisibilityRules;
  actorUserId: UUID;
}

export interface UpsertLessonResourceInput {
  lessonId: UUID;
  resourceId?: UUID;
  label: string;
  resourceType: ResourceType;
  uri: string;
  orderIndex?: number;
  visibilityRules?: VisibilityRules;
  actorUserId: UUID;
}

export interface ReorderLessonContentInput {
  lessonId: UUID;
  orderedLessonContentIds: UUID[];
  actorUserId: UUID;
}

export interface LearnerContext {
  tenantId: UUID;
  organizationId?: UUID;
  cohortIds?: UUID[];
  roleIds?: string[];
  isEnrolled?: boolean;
  currentAt?: string;
}
