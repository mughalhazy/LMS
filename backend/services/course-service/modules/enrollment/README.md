# Course Enrollment Module

Implements tenant-scoped enrollment workflows for the Course Service.

> **Boundary note:** This module defines its own enrollment status lifecycle (`enrolled`, `waitlisted`, `completed`, `withdrawn`, `cancelled`). The canonical enrollment-service uses a different lifecycle (`assigned` → `active` → `completed`). This module is internal to the course-service domain only — it does not replace or duplicate the enrollment-service. Reconciliation of status terminology with the canonical enrollment-service lifecycle is a pending normalisation action.

## Features

- Enroll user to course with duplicate active-enrollment protection.
- Unenroll user from course by transitioning enrollment status to `withdrawn`.
- Enrollment status tracking (`enrolled`, `waitlisted`, `completed`, `withdrawn`, `cancelled`).
- Strict tenant scoping via `tenantId` on all repository and service operations.

## Entities Used

- `Enrollment`
  - `enrollmentId`
  - `tenantId`
  - `userId`
  - `courseId`
  - `status`
  - `enrolledAt`
  - `updatedAt`
  - `unenrolledAt?`

## API Endpoints

- `POST /enrollments`
  - Enroll user to course.
  - Requires header: `x-tenant-id`.
  - Body: `{ userId, courseId, status? }`.

- `DELETE /enrollments/{enrollmentId}`
  - Unenroll user from course.
  - Requires header: `x-tenant-id`.

- `PATCH /enrollments/{enrollmentId}`
  - Update enrollment status.
  - Requires header: `x-tenant-id`.
  - Body: `{ status }`.

- `GET /enrollments/{enrollmentId}`
  - Get enrollment details for tenant.

- `GET /enrollments?userId=&courseId=&status=`
  - List tenant enrollments with optional filters.
