import {
  CompletionStatus,
  LessonStatus,
  ScormTrackingState,
  ScoreTracking,
  TrackingContext,
} from './tracking.entities';
import {
  CompletionStatusUpdatedEvent,
  LessonCompletionTrackedEvent,
  LessonStatusTrackedEvent,
  ScoreTrackedEvent,
  SessionTimeTrackedEvent,
  TrackingEvents,
} from './tracking.events';
import { EventBus, InMemoryEventBus } from './event-bus';
import { NoopProgressServiceClient, ProgressServiceClient } from './progress-service.client';

const DEFAULT_SCORE: Required<ScoreTracking> = {
  raw: 0,
  min: 0,
  max: 100,
  scaled: 0,
};

export class ScormTrackingModule {
  private readonly stateByRegistration = new Map<string, ScormTrackingState>();

  constructor(
    private readonly progressService: ProgressServiceClient = new NoopProgressServiceClient(),
    private readonly eventBus: EventBus = new InMemoryEventBus(),
  ) {}

  initialize(context: TrackingContext): ScormTrackingState {
    const state: ScormTrackingState = {
      ...context,
      sessionId: context.sessionId ?? context.registrationId,
      scoId: context.scoId ?? context.lessonId,
      commitSequence: 0,
      lessonStatus: LessonStatus.NotAttempted,
      completionStatus: CompletionStatus.Unknown,
      score: { ...DEFAULT_SCORE },
      sessionTime: {
        sessionSeconds: 0,
        totalSeconds: 0,
      },
      progressPercentage: 0,
      updatedAt: new Date().toISOString(),
    };

    this.stateByRegistration.set(context.registrationId, state);
    return state;
  }

  async trackLessonStatus(registrationId: string, lessonStatus: LessonStatus): Promise<ScormTrackingState> {
    const state = this.mustGetState(registrationId);
    state.lessonStatus = lessonStatus;
    state.completionStatus = this.deriveCompletionStatus(state);
    state.progressPercentage = this.deriveProgressPercentage(state);
    state.commitSequence += 1;
    state.updatedAt = new Date().toISOString();

    await this.progressService.upsertLessonProgress(state);

    const event: LessonStatusTrackedEvent = {
      eventName: TrackingEvents.LessonStatusTracked,
      ...this.eventBase(state),
      lessonStatus,
    };

    await this.eventBus.publish({ eventName: event.eventName, payload: event });
    return state;
  }

  async trackScore(registrationId: string, score: ScoreTracking): Promise<ScormTrackingState> {
    const state = this.mustGetState(registrationId);

    state.score = {
      raw: score.raw ?? state.score.raw,
      min: score.min ?? state.score.min,
      max: score.max ?? state.score.max,
      scaled: this.normalizeScaledScore(score, state.score),
    };

    state.completionStatus = this.deriveCompletionStatus(state);
    state.progressPercentage = this.deriveProgressPercentage(state);
    state.commitSequence += 1;
    state.updatedAt = new Date().toISOString();

    await this.progressService.upsertLessonProgress(state);

    const event: ScoreTrackedEvent = {
      eventName: TrackingEvents.ScoreTracked,
      ...this.eventBase(state),
      score: state.score,
      masteryScore: null,
      successStatus: this.toSuccessStatus(state.completionStatus),
      isMasteryAchieved: null,
    };

    await this.eventBus.publish({ eventName: event.eventName, payload: event });
    return state;
  }

  async trackSessionTime(registrationId: string, sessionTime: string): Promise<ScormTrackingState> {
    const state = this.mustGetState(registrationId);
    const increment = this.parseScormDurationToSeconds(sessionTime);
    state.sessionTime.sessionSeconds = increment;
    state.sessionTime.totalSeconds += increment;
    state.commitSequence += 1;
    state.updatedAt = new Date().toISOString();

    await this.progressService.upsertLessonProgress(state);

    const event: SessionTimeTrackedEvent = {
      eventName: TrackingEvents.SessionTimeTracked,
      ...this.eventBase(state),
      sessionTime: state.sessionTime,
      progress: {
        completionPercent: state.progressPercentage,
        status: this.toProgressStatus(state.completionStatus),
      },
      commitSequence: state.commitSequence,
    };

    await this.eventBus.publish({ eventName: event.eventName, payload: event });
    return state;
  }

  async updateCompletionStatus(registrationId: string): Promise<ScormTrackingState> {
    const state = this.mustGetState(registrationId);
    state.completionStatus = this.deriveCompletionStatus(state);
    state.progressPercentage = this.deriveProgressPercentage(state);

    if (state.completionStatus === CompletionStatus.Completed || state.completionStatus === CompletionStatus.Passed) {
      state.completedAt = state.completedAt ?? new Date().toISOString();
    }

    state.commitSequence += 1;
    state.updatedAt = new Date().toISOString();

    await this.progressService.updateCompletionStatus({
      tenantId: state.tenantId,
      learnerId: state.learnerId,
      courseId: state.courseId,
      lessonId: state.lessonId,
      enrollmentId: state.enrollmentId,
      completionStatus: state.completionStatus,
      score: state.score.raw,
      timeSpentSeconds: state.sessionTime.totalSeconds,
      completedAt: state.completedAt,
      attemptCount: state.attemptNumber,
    });

    const completionEvent: CompletionStatusUpdatedEvent = {
      eventName: TrackingEvents.CompletionStatusUpdated,
      ...this.eventBase(state),
      progress: {
        completionPercent: state.progressPercentage,
        status: this.toProgressStatus(state.completionStatus),
      },
      completionStatus: state.completionStatus,
      completedAt: state.completedAt,
      commitSequence: state.commitSequence,
    };

    await this.eventBus.publish({ eventName: completionEvent.eventName, payload: completionEvent });

    const lessonCompletionEvent: LessonCompletionTrackedEvent = {
      eventName: TrackingEvents.LessonCompletionTracked,
      ...this.eventBase(state),
      finalOutcome: this.toFinalOutcome(state.completionStatus),
      completionStatus: state.completionStatus,
      successStatus: this.toSuccessStatus(state.completionStatus),
      scoreScaled: state.score.scaled,
      totalTimeSeconds: state.sessionTime.totalSeconds,
      completedAt: state.completedAt,
      attemptLimitReached: false,
    };

    await this.eventBus.publish({ eventName: lessonCompletionEvent.eventName, payload: lessonCompletionEvent });

    return state;
  }

  getTrackingState(registrationId: string): ScormTrackingState {
    return this.mustGetState(registrationId);
  }

  private mustGetState(registrationId: string): ScormTrackingState {
    const state = this.stateByRegistration.get(registrationId);
    if (!state) {
      throw new Error(`Tracking state not initialized for registration ${registrationId}`);
    }

    return state;
  }

  private deriveCompletionStatus(state: ScormTrackingState): CompletionStatus {
    if (state.lessonStatus === LessonStatus.Failed) {
      return CompletionStatus.Failed;
    }

    if (state.lessonStatus === LessonStatus.Passed) {
      return CompletionStatus.Passed;
    }

    if (state.lessonStatus === LessonStatus.Completed) {
      return CompletionStatus.Completed;
    }

    if (state.score.scaled >= 1 || state.score.raw >= 100) {
      return CompletionStatus.Passed;
    }

    if (state.score.scaled > 0 || state.lessonStatus === LessonStatus.Incomplete) {
      return CompletionStatus.Incomplete;
    }

    return CompletionStatus.Unknown;
  }

  private deriveProgressPercentage(state: ScormTrackingState): number {
    if (state.completionStatus === CompletionStatus.Completed || state.completionStatus === CompletionStatus.Passed) {
      return 100;
    }

    if (state.completionStatus === CompletionStatus.Failed) {
      return 100;
    }

    return Math.max(0, Math.min(99, Math.round(state.score.scaled * 100)));
  }

  private normalizeScaledScore(next: ScoreTracking, current: Required<ScoreTracking>): number {
    if (typeof next.scaled === 'number') {
      return Math.max(0, Math.min(1, next.scaled));
    }

    const raw = next.raw ?? current.raw;
    const min = next.min ?? current.min;
    const max = next.max ?? current.max;

    if (max <= min) {
      return current.scaled;
    }

    return Math.max(0, Math.min(1, (raw - min) / (max - min)));
  }

  /** Supports SCORM 1.2 HH:MM:SS(.SS) and SCORM 2004 ISO8601 duration PT#H#M#S */
  private parseScormDurationToSeconds(duration: string): number {
    const scorm2004 = /^PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?$/;
    const scorm12 = /^(\d{2,4}):(\d{2}):(\d{2})(?:\.(\d+))?$/;

    const match2004 = duration.match(scorm2004);
    if (match2004) {
      const hours = Number(match2004[1] ?? 0);
      const minutes = Number(match2004[2] ?? 0);
      const seconds = Number(match2004[3] ?? 0);
      return Math.round(hours * 3600 + minutes * 60 + seconds);
    }

    const match12 = duration.match(scorm12);
    if (match12) {
      const hours = Number(match12[1]);
      const minutes = Number(match12[2]);
      const seconds = Number(match12[3]);
      return Math.round(hours * 3600 + minutes * 60 + seconds);
    }

    throw new Error(`Unsupported SCORM session_time format: ${duration}`);
  }

  private toProgressStatus(completionStatus: CompletionStatus): 'not_started' | 'in_progress' | 'completed' | 'passed' | 'failed' {
    if (completionStatus === CompletionStatus.Completed) {
      return 'completed';
    }

    if (completionStatus === CompletionStatus.Passed) {
      return 'passed';
    }

    if (completionStatus === CompletionStatus.Failed) {
      return 'failed';
    }

    if (completionStatus === CompletionStatus.Incomplete) {
      return 'in_progress';
    }

    return 'not_started';
  }

  private toSuccessStatus(completionStatus: CompletionStatus): 'passed' | 'failed' | 'unknown' {
    if (completionStatus === CompletionStatus.Passed || completionStatus === CompletionStatus.Completed) {
      return 'passed';
    }

    if (completionStatus === CompletionStatus.Failed) {
      return 'failed';
    }

    return 'unknown';
  }

  private toFinalOutcome(completionStatus: CompletionStatus): 'completed' | 'passed' | 'failed' | 'incomplete' {
    if (completionStatus === CompletionStatus.Completed) {
      return 'completed';
    }

    if (completionStatus === CompletionStatus.Passed) {
      return 'passed';
    }

    if (completionStatus === CompletionStatus.Failed) {
      return 'failed';
    }

    return 'incomplete';
  }

  private eventBase(state: ScormTrackingState) {
    return {
      eventId: `${state.registrationId}-${state.commitSequence}`,
      occurredAt: new Date().toISOString(),
      tenantId: state.tenantId,
      learnerId: state.learnerId,
      courseId: state.courseId,
      registrationId: state.registrationId,
      sessionId: state.sessionId,
      attemptNumber: state.attemptNumber,
      scoId: state.scoId,
    };
  }
}
