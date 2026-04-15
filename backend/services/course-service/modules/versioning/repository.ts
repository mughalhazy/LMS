import { CourseVersion, CourseVersionPointer, VersionAuditEvent } from "./types";

export interface CourseVersionRepository {
  getVersions(tenantId: string, courseId: string): Promise<CourseVersion[]>;
  getVersion(tenantId: string, courseId: string, versionNumber: number): Promise<CourseVersion | undefined>;
  saveVersion(version: CourseVersion): Promise<void>;
  updateVersion(version: CourseVersion): Promise<void>;
  getPointer(tenantId: string, courseId: string): Promise<CourseVersionPointer | undefined>;
  savePointer(pointer: CourseVersionPointer): Promise<void>;
  appendAuditEvent(event: VersionAuditEvent): Promise<void>;
  getAuditEvents(tenantId: string, courseId: string): Promise<VersionAuditEvent[]>;
}

export class InMemoryCourseVersionRepository implements CourseVersionRepository {
  private readonly versions = new Map<string, CourseVersion[]>();
  private readonly pointers = new Map<string, CourseVersionPointer>();
  private readonly auditEvents = new Map<string, VersionAuditEvent[]>();

  async getVersions(tenantId: string, courseId: string): Promise<CourseVersion[]> {
    return [...(this.versions.get(this.key(tenantId, courseId)) ?? [])].sort(
      (a, b) => b.versionNumber - a.versionNumber,
    );
  }

  async getVersion(tenantId: string, courseId: string, versionNumber: number): Promise<CourseVersion | undefined> {
    return (this.versions.get(this.key(tenantId, courseId)) ?? []).find((v) => v.versionNumber === versionNumber);
  }

  async saveVersion(version: CourseVersion): Promise<void> {
    const mapKey = this.key(version.tenantId, version.courseId);
    const versions = this.versions.get(mapKey) ?? [];
    versions.push(version);
    this.versions.set(mapKey, versions);
  }

  async updateVersion(version: CourseVersion): Promise<void> {
    const mapKey = this.key(version.tenantId, version.courseId);
    const versions = this.versions.get(mapKey) ?? [];
    const index = versions.findIndex((v) => v.versionNumber === version.versionNumber);
    if (index < 0) {
      throw new Error(`Version ${version.versionNumber} not found for course ${version.courseId}`);
    }

    versions[index] = version;
    this.versions.set(mapKey, versions);
  }

  async getPointer(tenantId: string, courseId: string): Promise<CourseVersionPointer | undefined> {
    return this.pointers.get(this.key(tenantId, courseId));
  }

  async savePointer(pointer: CourseVersionPointer): Promise<void> {
    this.pointers.set(this.key(pointer.tenantId, pointer.courseId), pointer);
  }

  async appendAuditEvent(event: VersionAuditEvent): Promise<void> {
    const mapKey = this.key(event.tenantId, event.courseId);
    const events = this.auditEvents.get(mapKey) ?? [];
    events.push(event);
    this.auditEvents.set(mapKey, events);
  }

  async getAuditEvents(tenantId: string, courseId: string): Promise<VersionAuditEvent[]> {
    return [...(this.auditEvents.get(this.key(tenantId, courseId)) ?? [])].sort((a, b) =>
      b.occurredAt.localeCompare(a.occurredAt),
    );
  }

  private key(tenantId: string, courseId: string): string {
    return `${tenantId}:${courseId}`;
  }
}
