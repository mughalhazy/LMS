import {
  CourseCompletedPayload,
  EventConsumer,
  EventEnvelope,
  ProgressProjectionStore,
} from './event-consumer.types';

/**
 * Consumes `course_completed` and projects CourseCompletionTracked data.
 */
export class CourseCompletedConsumer
  implements EventConsumer<CourseCompletedPayload>
{
  public readonly eventName = 'course_completed' as const;

  public constructor(private readonly store: ProgressProjectionStore) {}

  public async handle(
    event: EventEnvelope<CourseCompletedPayload>,
  ): Promise<void> {
    const { payload } = event;

    await this.store.completeCourse({
      tenant_id: payload.tenant_id,
      learner_id: payload.learner_id,
      course_id: payload.course_id,
      enrollment_id: payload.enrollment_id,
      completion_status: 'completed',
      final_score: payload.final_score ?? null,
      started_at: payload.started_at ?? null,
      completed_at: payload.completed_at,
      total_time_spent_seconds: payload.total_time_spent_seconds ?? 0,
      certificate_id: payload.certificate_id ?? null,
    });
  }
}
