import {
  Enrollment,
  EnrollUserInput,
  EnrollmentFilter,
  EnrollmentStatus,
  UnenrollUserInput,
  UpdateEnrollmentStatusInput,
} from './types';
import { EnrollmentRepository } from './repository';

const ACTIVE_ENROLLMENT_STATUSES: EnrollmentStatus[] = ['enrolled', 'waitlisted', 'completed'];

export class EnrollmentService {
  constructor(private readonly repository: EnrollmentRepository) {}

  enrollUser(input: EnrollUserInput): Enrollment {
    const existing = this.repository.findByUserAndCourse(input.tenantId, input.userId, input.courseId);
    if (existing && ACTIVE_ENROLLMENT_STATUSES.includes(existing.status)) {
      throw new Error('User is already enrolled in this course for the tenant');
    }

    if (existing && ['withdrawn', 'cancelled'].includes(existing.status)) {
      existing.status = input.status ?? 'enrolled';
      existing.unenrolledAt = undefined;
      return this.repository.save(existing);
    }

    return this.repository.create({
      tenantId: input.tenantId,
      userId: input.userId,
      courseId: input.courseId,
      status: input.status ?? 'enrolled',
    });
  }

  unenrollUser(input: UnenrollUserInput): Enrollment {
    const enrollment = this.repository.findById(input.tenantId, input.enrollmentId);
    if (!enrollment) {
      throw new Error('Enrollment not found for tenant');
    }

    enrollment.status = 'withdrawn';
    enrollment.unenrolledAt = new Date().toISOString();
    return this.repository.save(enrollment);
  }

  updateEnrollmentStatus(input: UpdateEnrollmentStatusInput): Enrollment {
    const enrollment = this.repository.findById(input.tenantId, input.enrollmentId);
    if (!enrollment) {
      throw new Error('Enrollment not found for tenant');
    }

    enrollment.status = input.status;
    if (input.status === 'withdrawn' || input.status === 'cancelled') {
      enrollment.unenrolledAt = new Date().toISOString();
    }

    return this.repository.save(enrollment);
  }

  getEnrollment(tenantId: string, enrollmentId: string): Enrollment {
    const enrollment = this.repository.findById(tenantId, enrollmentId);
    if (!enrollment) {
      throw new Error('Enrollment not found for tenant');
    }

    return enrollment;
  }

  listEnrollments(filter: EnrollmentFilter): Enrollment[] {
    return this.repository.list(filter);
  }
}
