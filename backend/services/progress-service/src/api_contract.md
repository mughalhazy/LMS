# Progress Service API Endpoints

Base path: `/api/v1/progress`

## 1) Track lesson completion
- **POST** `/api/v1/progress/lessons/completion`
- Request body fields:
  - `tenant_id`
  - `learner_id`
  - `course_id`
  - `lesson_id`
  - `enrollment_id`
  - `completion_status`
  - `score`
  - `time_spent_seconds`
  - `attempt_count`
- Emits:
  - `LessonCompletionTracked`
  - recomputed `CourseCompletionTracked`
  - recomputed `LearningPathProgressUpdated`

## 2) Assign learning path to learner
- **POST** `/api/v1/progress/learning-paths/assign`
- Request body fields:
  - `tenant_id`
  - `learner_id`
  - `learning_path_id`
  - `assigned_course_ids`
  - `expected_completion_date` (optional)
- Emits:
  - initial `LearningPathProgressUpdated`

## 3) Get learner progress (tenant scoped)
- **GET** `/api/v1/progress/learners/{learner_id}?tenant_id={tenant_id}`
- Response sections:
  - `courses`
  - `lessons`
  - `learning_paths`

## 4) Get course progress for learner
- **GET** `/api/v1/progress/learners/{learner_id}/courses/{course_id}?tenant_id={tenant_id}`
- Response:
  - `completion_status`
  - `final_score`
  - `started_at`
  - `completed_at`
  - `total_time_spent_seconds`
  - `certificate_id`
