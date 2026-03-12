import { CompletionStatus, ScormTrackingState } from './tracking.entities';

export interface ProgressServiceClient {
  upsertLessonProgress(state: ScormTrackingState): Promise<void>;
  updateCompletionStatus(input: {
    tenantId: string;
    learnerId: string;
    courseId: string;
    lessonId: string;
    enrollmentId: string;
    completionStatus: CompletionStatus;
    score: number;
    timeSpentSeconds: number;
    completedAt?: string;
    attemptCount: number;
  }): Promise<void>;
}

/**
 * Default no-op integration adapter to keep module wiring safe in lower environments.
 * Replace with HTTP/gRPC implementation in service composition root.
 */
export class NoopProgressServiceClient implements ProgressServiceClient {
  async upsertLessonProgress(_state: ScormTrackingState): Promise<void> {
    return;
  }

  async updateCompletionStatus(_input: {
    tenantId: string;
    learnerId: string;
    courseId: string;
    lessonId: string;
    enrollmentId: string;
    completionStatus: CompletionStatus;
    score: number;
    timeSpentSeconds: number;
    completedAt?: string;
    attemptCount: number;
  }): Promise<void> {
    return;
  }
}
