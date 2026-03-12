import {
  EventConsumer,
  EventEnvelope,
  LessonCompletedPayload,
  ProgressProjectionStore,
} from './event-consumer.types';

/**
 * Consumes `lesson_completed` and projects LessonCompletionTracked data for downstream analytics/profile consumers.
 */
export class LessonCompletedConsumer
  implements EventConsumer<LessonCompletedPayload>
{
  public readonly eventName = 'lesson_completed' as const;

  public constructor(private readonly store: ProgressProjectionStore) {}

  public async handle(
    event: EventEnvelope<LessonCompletedPayload>,
  ): Promise<void> {
    const { payload } = event;

    await this.store.upsertLessonProgress({
      tenant_id: payload.tenant_id,
      learner_id: payload.learner_id,
      course_id: payload.course_id,
      lesson_id: payload.lesson_id,
      enrollment_id: payload.enrollment_id,
      completion_status: 'completed',
      score: payload.score ?? null,
      time_spent_seconds: payload.time_spent_seconds ?? 0,
      completed_at: payload.completed_at,
      attempt_count: payload.attempt_count ?? 1,
    });
  }
}
