import {
  EnrollmentLifecycleChangedPayload,
  EventConsumer,
  EventEnvelope,
  ProgressProjectionStore,
} from './event-consumer.types';

/**
 * Consumes `enrollment_lifecycle_changed` and creates/updates learner enrollment baseline for progress tracking.
 */
export class CourseEnrolledConsumer
  implements EventConsumer<EnrollmentLifecycleChangedPayload>
{
  public readonly eventName = 'enrollment_lifecycle_changed' as const;

  public constructor(private readonly store: ProgressProjectionStore) {}

  public async handle(
    event: EventEnvelope<EnrollmentLifecycleChangedPayload>,
  ): Promise<void> {
    const { payload } = event;

    const statusMap: Record<EnrollmentLifecycleChangedPayload['status'], 'enrolled' | 'in_progress' | 'completed' | 'cancelled'> = {
      assigned: 'enrolled',
      active: 'in_progress',
      completed: 'completed',
      cancelled: 'cancelled',
    };

    await this.store.upsertCourseEnrollment({
      tenant_id: payload.tenant_id,
      learner_id: payload.learner_id,
      course_id: payload.course_id,
      enrollment_id: payload.id,
      status: statusMap[payload.status],
      enrolled_at: payload.created_at,
    });
  }
}
