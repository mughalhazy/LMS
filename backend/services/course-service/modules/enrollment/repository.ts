import { randomUUID } from 'crypto';
import { Enrollment, EnrollmentFilter, EnrollmentStatus } from './types';

export interface EnrollmentRepository {
  create(params: { tenantId: string; userId: string; courseId: string; status: EnrollmentStatus }): Enrollment;
  findById(tenantId: string, enrollmentId: string): Enrollment | undefined;
  findByUserAndCourse(tenantId: string, userId: string, courseId: string): Enrollment | undefined;
  list(filter: EnrollmentFilter): Enrollment[];
  save(enrollment: Enrollment): Enrollment;
}

/**
 * Shared-schema style repository with strict tenant filtering for every operation.
 */
export class InMemoryEnrollmentRepository implements EnrollmentRepository {
  private readonly records = new Map<string, Enrollment>();

  create(params: { tenantId: string; userId: string; courseId: string; status: EnrollmentStatus }): Enrollment {
    const now = new Date().toISOString();
    const enrollment: Enrollment = {
      enrollmentId: randomUUID(),
      tenantId: params.tenantId,
      userId: params.userId,
      courseId: params.courseId,
      status: params.status,
      enrolledAt: now,
      updatedAt: now,
    };

    this.records.set(this.key(params.tenantId, enrollment.enrollmentId), enrollment);
    return enrollment;
  }

  findById(tenantId: string, enrollmentId: string): Enrollment | undefined {
    return this.records.get(this.key(tenantId, enrollmentId));
  }

  findByUserAndCourse(tenantId: string, userId: string, courseId: string): Enrollment | undefined {
    for (const enrollment of this.records.values()) {
      if (enrollment.tenantId !== tenantId) continue;
      if (enrollment.userId === userId && enrollment.courseId === courseId) {
        return enrollment;
      }
    }

    return undefined;
  }

  list(filter: EnrollmentFilter): Enrollment[] {
    return [...this.records.values()].filter((enrollment) => {
      if (enrollment.tenantId !== filter.tenantId) return false;
      if (filter.userId && enrollment.userId !== filter.userId) return false;
      if (filter.courseId && enrollment.courseId !== filter.courseId) return false;
      if (filter.status && enrollment.status !== filter.status) return false;
      return true;
    });
  }

  save(enrollment: Enrollment): Enrollment {
    enrollment.updatedAt = new Date().toISOString();
    this.records.set(this.key(enrollment.tenantId, enrollment.enrollmentId), enrollment);
    return enrollment;
  }

  private key(tenantId: string, enrollmentId: string): string {
    return `${tenantId}:${enrollmentId}`;
  }
}
