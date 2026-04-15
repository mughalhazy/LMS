import {
  AttachLessonContentInput,
  LearnerContext,
  ReorderLessonContentInput,
  UpsertLessonResourceInput,
  UUID,
} from "./entities";
import { LessonContentService } from "./content.service";

export class LessonContentController {
  constructor(private readonly service: LessonContentService) {}

  // POST /lessons/:lessonId/content
  attachContent(payload: AttachLessonContentInput) {
    return this.service.attachContent(payload);
  }

  // PUT /lessons/:lessonId/resources/:resourceId?
  upsertResource(payload: UpsertLessonResourceInput) {
    return this.service.upsertResource(payload);
  }

  // PUT /lessons/:lessonId/content/order
  reorderContent(payload: ReorderLessonContentInput) {
    return this.service.reorderContent(payload);
  }

  // GET /lessons/:lessonId/content/visible
  listVisibleContent(lessonId: UUID, context: LearnerContext) {
    return this.service.listVisibleLessonContent(lessonId, context);
  }
}
