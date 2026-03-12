export type ScormVersion = '1.2' | '2004';

export enum LessonStatus {
  NotAttempted = 'not_attempted',
  Incomplete = 'incomplete',
  Completed = 'completed',
  Passed = 'passed',
  Failed = 'failed',
  Browsed = 'browsed',
}

export enum CompletionStatus {
  Unknown = 'unknown',
  Incomplete = 'incomplete',
  Completed = 'completed',
  Passed = 'passed',
  Failed = 'failed',
}

export interface ScoreTracking {
  raw?: number;
  min?: number;
  max?: number;
  scaled?: number;
}

export interface SessionTimeTracking {
  /** Increment from current runtime API call, in seconds. */
  sessionSeconds: number;
  /** Accumulated attempt duration, in seconds. */
  totalSeconds: number;
}

export interface ScormTrackingState {
  tenantId: string;
  learnerId: string;
  courseId: string;
  lessonId: string;
  enrollmentId: string;
  registrationId: string;
  attemptNumber: number;
  scormVersion: ScormVersion;
  lessonStatus: LessonStatus;
  completionStatus: CompletionStatus;
  score: Required<ScoreTracking>;
  sessionTime: SessionTimeTracking;
  progressPercentage: number;
  completedAt?: string;
  updatedAt: string;
}

export interface TrackingContext {
  tenantId: string;
  learnerId: string;
  courseId: string;
  lessonId: string;
  enrollmentId: string;
  registrationId: string;
  attemptNumber: number;
  scormVersion: ScormVersion;
}
