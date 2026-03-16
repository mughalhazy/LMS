import { LessonContentItem, LessonResource, UUID } from "./entities";

export interface LessonContentRepository {
  getContentByLessonId(tenantId: UUID, lessonId: UUID): Promise<LessonContentItem[]>;
  createContent(item: LessonContentItem): Promise<LessonContentItem>;
  updateContent(item: LessonContentItem): Promise<LessonContentItem>;
  findContentById(tenantId: UUID, lessonContentId: UUID): Promise<LessonContentItem | null>;

  getResourcesByLessonId(tenantId: UUID, lessonId: UUID): Promise<LessonResource[]>;
  createResource(resource: LessonResource): Promise<LessonResource>;
  updateResource(resource: LessonResource): Promise<LessonResource>;
  findResourceById(tenantId: UUID, resourceId: UUID): Promise<LessonResource | null>;
}

export class InMemoryLessonContentRepository implements LessonContentRepository {
  private readonly content: LessonContentItem[] = [];

  private readonly resources: LessonResource[] = [];

  async getContentByLessonId(tenantId: UUID, lessonId: UUID): Promise<LessonContentItem[]> {
    return this.content
      .filter((item) => item.tenantId === tenantId && item.lessonId === lessonId)
      .sort((a, b) => a.orderIndex - b.orderIndex);
  }

  async createContent(item: LessonContentItem): Promise<LessonContentItem> {
    this.content.push(item);
    return item;
  }

  async updateContent(item: LessonContentItem): Promise<LessonContentItem> {
    const index = this.content.findIndex(
      (entry) => entry.tenantId === item.tenantId && entry.lessonContentId === item.lessonContentId,
    );
    if (index >= 0) {
      this.content[index] = item;
    }
    return item;
  }

  async findContentById(tenantId: UUID, lessonContentId: UUID): Promise<LessonContentItem | null> {
    return this.content.find((item) => item.tenantId === tenantId && item.lessonContentId === lessonContentId) ?? null;
  }

  async getResourcesByLessonId(tenantId: UUID, lessonId: UUID): Promise<LessonResource[]> {
    return this.resources
      .filter((resource) => resource.tenantId === tenantId && resource.lessonId === lessonId)
      .sort((a, b) => a.orderIndex - b.orderIndex);
  }

  async createResource(resource: LessonResource): Promise<LessonResource> {
    this.resources.push(resource);
    return resource;
  }

  async updateResource(resource: LessonResource): Promise<LessonResource> {
    const index = this.resources.findIndex(
      (entry) => entry.tenantId === resource.tenantId && entry.resourceId === resource.resourceId,
    );
    if (index >= 0) {
      this.resources[index] = resource;
    }
    return resource;
  }

  async findResourceById(tenantId: UUID, resourceId: UUID): Promise<LessonResource | null> {
    return this.resources.find((resource) => resource.tenantId === tenantId && resource.resourceId === resourceId) ?? null;
  }
}
