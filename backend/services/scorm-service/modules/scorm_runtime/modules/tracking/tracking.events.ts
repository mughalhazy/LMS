import { CompletionStatus, LessonStatus, ScoreTracking, SessionTimeTracking } from './tracking.entities';

export const TrackingEvents = {
  LessonStatusTracked: 'scorm_progress_updated',
  ScoreTracked: 'scorm_score_recorded',
  SessionTimeTracked: 'scorm_progress_updated',
  CompletionStatusUpdated: 'scorm_progress_updated',
  LessonCompletionTracked: 'scorm_session_completed',
} as const;

export interface BaseTrackingEvent {
  eventId: string;
  occurredAt: string;
  tenantId: string;
  learnerId: string;
  courseId: string;
  registrationId: string;
  sessionId: string;
  attemptNumber: number;
  scoId: string;
}

export interface LessonStatusTrackedEvent extends BaseTrackingEvent {
  eventName: typeof TrackingEvents.LessonStatusTracked;
  lessonStatus: LessonStatus;
}

export interface ScoreTrackedEvent extends BaseTrackingEvent {
  eventName: typeof TrackingEvents.ScoreTracked;
  score: Required<ScoreTracking>;
  masteryScore: number | null;
  successStatus: 'passed' | 'failed' | 'unknown';
  isMasteryAchieved: boolean | null;
}

export interface SessionTimeTrackedEvent extends BaseTrackingEvent {
  eventName: typeof TrackingEvents.SessionTimeTracked;
  sessionTime: SessionTimeTracking;
  progress: {
    completionPercent: number;
    status: 'not_started' | 'in_progress' | 'completed' | 'passed' | 'failed';
  };
  commitSequence: number;
}

export interface CompletionStatusUpdatedEvent extends BaseTrackingEvent {
  eventName: typeof TrackingEvents.CompletionStatusUpdated;
  completionStatus: CompletionStatus;
  progress: {
    completionPercent: number;
    status: 'not_started' | 'in_progress' | 'completed' | 'passed' | 'failed';
  };
  completedAt?: string;
  commitSequence: number;
}

export interface LessonCompletionTrackedEvent extends BaseTrackingEvent {
  eventName: typeof TrackingEvents.LessonCompletionTracked;
  finalOutcome: 'completed' | 'passed' | 'failed' | 'incomplete';
  completionStatus: CompletionStatus;
  successStatus: 'passed' | 'failed' | 'unknown';
  scoreScaled: number;
  totalTimeSeconds: number;
  completedAt?: string;
  attemptLimitReached: boolean;
}
