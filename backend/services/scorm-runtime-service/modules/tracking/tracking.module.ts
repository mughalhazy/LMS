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
  ScormTrackingEvent,
  SessionTimeTrackedEvent,
  TrackingEvents,
} from './tracking.events';
import { NoopProgressServiceClient, ProgressServiceClient } from './progress-service.client';

interface EventBus {
  emit<TEvent extends ScormTrackingEvent>(event: TEvent): Promise<void> | void;
}

class InMemoryEventBus implements EventBus {
  async emit<TEvent extends ScormTrackingEvent>(_event: TEvent): Promise<void> {
    return;
  }
}

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
    state.updatedAt = new Date().toISOString();

    await this.progressService.upsertLessonProgress(state);

    const event: LessonStatusTrackedEvent = {
      eventName: TrackingEvents.LessonStatusTracked,
      ...this.eventBase(state),
      lessonStatus,
    };

    await this.eventBus.emit(event);
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
    state.updatedAt = new Date().toISOString();

    await this.progressService.upsertLessonProgress(state);

    const event: ScoreTrackedEvent = {
      eventName: TrackingEvents.ScoreTracked,
      ...this.eventBase(state),
      score: state.score,
    };

    await this.eventBus.emit(event);
    return state;
  }

  async trackSessionTime(registrationId: string, sessionTime: string): Promise<ScormTrackingState> {
    const state = this.mustGetState(registrationId);
    const increment = this.parseScormDurationToSeconds(sessionTime);
    state.sessionTime.sessionSeconds = increment;
    state.sessionTime.totalSeconds += increment;
    state.updatedAt = new Date().toISOString();

    await this.progressService.upsertLessonProgress(state);

    const event: SessionTimeTrackedEvent = {
      eventName: TrackingEvents.SessionTimeTracked,
      ...this.eventBase(state),
      sessionTime: state.sessionTime,
    };

    await this.eventBus.emit(event);
    return state;
  }

  async updateCompletionStatus(registrationId: string): Promise<ScormTrackingState> {
    const state = this.mustGetState(registrationId);
    state.completionStatus = this.deriveCompletionStatus(state);
    state.progressPercentage = this.deriveProgressPercentage(state);

    if (state.completionStatus === CompletionStatus.Completed || state.completionStatus === CompletionStatus.Passed) {
      state.completedAt = state.completedAt ?? new Date().toISOString();
    }

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
      completionStatus: state.completionStatus,
      progressPercentage: state.progressPercentage,
      completedAt: state.completedAt,
    };

    await this.eventBus.emit(completionEvent);

    const lessonCompletionEvent: LessonCompletionTrackedEvent = {
      eventName: TrackingEvents.LessonCompletionTracked,
      ...this.eventBase(state),
      completionStatus: state.completionStatus,
      score: state.score.raw,
      timeSpentSeconds: state.sessionTime.totalSeconds,
      completedAt: state.completedAt,
    };

    await this.eventBus.emit(lessonCompletionEvent);

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

  private eventBase(state: ScormTrackingState) {
    return {
      tenantId: state.tenantId,
      learnerId: state.learnerId,
      courseId: state.courseId,
      lessonId: state.lessonId,
      enrollmentId: state.enrollmentId,
      registrationId: state.registrationId,
      attemptNumber: state.attemptNumber,
      emittedAt: new Date().toISOString(),
    };
  }
}
