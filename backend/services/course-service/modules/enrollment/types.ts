export type EnrollmentStatus = 'enrolled' | 'waitlisted' | 'completed' | 'withdrawn' | 'cancelled';

export interface Enrollment {
  enrollmentId: string;
  tenantId: string;
  userId: string;
  courseId: string;
  status: EnrollmentStatus;
  enrolledAt: string;
  updatedAt: string;
  unenrolledAt?: string;
}

export interface EnrollUserInput {
  tenantId: string;
  userId: string;
  courseId: string;
  status?: EnrollmentStatus;
}

export interface UnenrollUserInput {
  tenantId: string;
  enrollmentId: string;
}

export interface UpdateEnrollmentStatusInput {
  tenantId: string;
  enrollmentId: string;
  status: EnrollmentStatus;
}

export interface EnrollmentFilter {
  tenantId: string;
  userId?: string;
  courseId?: string;
  status?: EnrollmentStatus;
}
