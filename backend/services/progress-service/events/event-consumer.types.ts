export type SupportedEventName =
  | 'lesson_completed'
  | 'course_completed'
  | 'enrollment_lifecycle_changed';

export interface EventEnvelope<TPayload> {
  event_name: SupportedEventName;
  occurred_at: string;
  payload: TPayload;
}

export interface ProgressProjectionStore {
  upsertLessonProgress(record: LessonProgressRecord): Promise<void>;
  upsertCourseEnrollment(record: CourseEnrollmentRecord): Promise<void>;
  completeCourse(record: CourseCompletionRecord): Promise<void>;
}

export interface LessonCompletedPayload {
  tenant_id: string;
  learner_id: string;
  course_id: string;
  lesson_id: string;
  enrollment_id: string;
  score?: number;
  time_spent_seconds?: number;
  completed_at: string;
  attempt_count?: number;
}

export interface EnrollmentLifecycleChangedPayload {
  id: string;
  tenant_id: string;
  learner_id: string;
  course_id: string;
  status: 'assigned' | 'active' | 'completed' | 'cancelled';
  created_at: string;
  updated_at: string;
}

export interface CourseCompletedPayload {
  tenant_id: string;
  learner_id: string;
  course_id: string;
  enrollment_id: string;
  final_score?: number;
  started_at?: string;
  completed_at: string;
  total_time_spent_seconds?: number;
  certificate_id?: string;
}

export interface LessonProgressRecord {
  tenant_id: string;
  learner_id: string;
  course_id: string;
  lesson_id: string;
  enrollment_id: string;
  completion_status: 'completed';
  score: number | null;
  time_spent_seconds: number;
  completed_at: string;
  attempt_count: number;
}

export interface CourseEnrollmentRecord {
  tenant_id: string;
  learner_id: string;
  course_id: string;
  enrollment_id: string;
  status: 'enrolled' | 'in_progress' | 'completed' | 'cancelled';
  enrolled_at: string;
}

export interface CourseCompletionRecord {
  tenant_id: string;
  learner_id: string;
  course_id: string;
  enrollment_id: string;
  completion_status: 'completed';
  final_score: number | null;
  started_at: string | null;
  completed_at: string;
  total_time_spent_seconds: number;
  certificate_id: string | null;
}

export interface EventConsumer<TPayload> {
  eventName: SupportedEventName;
  handle(event: EventEnvelope<TPayload>): Promise<void>;
}
