import { CompletionStatus, LessonStatus, ScoreTracking, SessionTimeTracking } from './tracking.entities';

export const TrackingEvents = {
  LessonStatusTracked: 'scorm.tracking.lesson_status_tracked',
  ScoreTracked: 'scorm.tracking.score_tracked',
  SessionTimeTracked: 'scorm.tracking.session_time_tracked',
  CompletionStatusUpdated: 'scorm.tracking.completion_status_updated',
  LessonCompletionTracked: 'progress.lesson_completion_tracked',
} as const;

export interface BaseTrackingEvent {
  tenantId: string;
  learnerId: string;
  courseId: string;
  lessonId: string;
  enrollmentId: string;
  registrationId: string;
  attemptNumber: number;
  emittedAt: string;
}

export interface LessonStatusTrackedEvent extends BaseTrackingEvent {
  eventName: typeof TrackingEvents.LessonStatusTracked;
  lessonStatus: LessonStatus;
}

export interface ScoreTrackedEvent extends BaseTrackingEvent {
  eventName: typeof TrackingEvents.ScoreTracked;
  score: Required<ScoreTracking>;
}

export interface SessionTimeTrackedEvent extends BaseTrackingEvent {
  eventName: typeof TrackingEvents.SessionTimeTracked;
  sessionTime: SessionTimeTracking;
}

export interface CompletionStatusUpdatedEvent extends BaseTrackingEvent {
  eventName: typeof TrackingEvents.CompletionStatusUpdated;
  completionStatus: CompletionStatus;
  progressPercentage: number;
  completedAt?: string;
}

export interface LessonCompletionTrackedEvent extends BaseTrackingEvent {
  eventName: typeof TrackingEvents.LessonCompletionTracked;
  completionStatus: CompletionStatus;
  score: number;
  timeSpentSeconds: number;
  completedAt?: string;
}

export type ScormTrackingEvent =
  | LessonStatusTrackedEvent
  | ScoreTrackedEvent
  | SessionTimeTrackedEvent
  | CompletionStatusUpdatedEvent
  | LessonCompletionTrackedEvent;
