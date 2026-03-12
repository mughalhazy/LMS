import { CourseCompletedConsumer } from './course-completed.consumer';
import { CourseEnrolledConsumer } from './course-enrolled.consumer';
import {
  EventConsumer,
  ProgressProjectionStore,
  SupportedEventName,
} from './event-consumer.types';
import { LessonCompletedConsumer } from './lesson-completed.consumer';

export interface ConsumerRegistry {
  readonly lesson_completed: EventConsumer<unknown>;
  readonly course_enrolled: EventConsumer<unknown>;
  readonly course_completed: EventConsumer<unknown>;
}

export const registerProgressEventConsumers = (
  store: ProgressProjectionStore,
): ConsumerRegistry => ({
  lesson_completed: new LessonCompletedConsumer(store),
  course_enrolled: new CourseEnrolledConsumer(store),
  course_completed: new CourseCompletedConsumer(store),
});

export const supportedProgressEvents: SupportedEventName[] = [
  'lesson_completed',
  'course_enrolled',
  'course_completed',
];
