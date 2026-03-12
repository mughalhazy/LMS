import {
  CourseEnrolledPayload,
  EventConsumer,
  EventEnvelope,
  ProgressProjectionStore,
} from './event-consumer.types';

/**
 * Consumes `course_enrolled` and creates/updates learner enrollment baseline for progress tracking.
 */
export class CourseEnrolledConsumer implements EventConsumer<CourseEnrolledPayload> {
  public readonly eventName = 'course_enrolled' as const;

  public constructor(private readonly store: ProgressProjectionStore) {}

  public async handle(event: EventEnvelope<CourseEnrolledPayload>): Promise<void> {
    const { payload } = event;

    await this.store.upsertCourseEnrollment({
      tenant_id: payload.tenant_id,
      learner_id: payload.learner_id,
      course_id: payload.course_id,
      enrollment_id: payload.enrollment_id,
      status: 'enrolled',
      enrolled_at: payload.enrolled_at,
    });
  }
}
