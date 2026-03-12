from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from .repository import AnalyticsRepository


class LearningAnalyticsService:
    def __init__(self, repository: AnalyticsRepository) -> None:
        self.repository = repository

    @staticmethod
    def _safe_rate(numerator: float, denominator: float) -> float:
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100, 2)

    def course_completion_analytics(
        self,
        course_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> dict:
        enrolled = [
            row
            for row in self.repository.list_enrollments(course_id, cohort_id)
            if row.enrollment_status in {"enrolled", "in_progress"}
        ]
        completion_rows = [
            row
            for row in self.repository.list_completions(course_id, start_at, end_at, cohort_id)
            if row.completion_status == "completed"
        ]
        completed_learner_ids = {row.learner_id for row in completion_rows}
        median_time_hours = 0.0
        if completion_rows:
            hours = sorted([row.total_time_spent_seconds / 3600 for row in completion_rows])
            mid = len(hours) // 2
            median_time_hours = round((hours[mid] if len(hours) % 2 else (hours[mid - 1] + hours[mid]) / 2), 2)

        return {
            "course_id": course_id,
            "cohort_id": cohort_id,
            "enrolled_learners": len({item.learner_id for item in enrolled}),
            "completed_learners": len(completed_learner_ids),
            "completion_rate": self._safe_rate(len(completed_learner_ids), len({item.learner_id for item in enrolled})),
            "median_time_to_complete_hours": median_time_hours,
        }

    def learner_engagement_metrics(
        self,
        course_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> dict:
        events = self.repository.list_activities(course_id, start_at, end_at, cohort_id)
        per_learner: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        for row in events:
            per_learner[row.learner_id]["active_minutes"] += row.active_minutes
            per_learner[row.learner_id]["content_interactions"] += row.content_interactions
            per_learner[row.learner_id]["assessment_attempts"] += row.assessment_attempts
            per_learner[row.learner_id]["discussion_actions"] += row.discussion_actions

        dimensions = ["active_minutes", "content_interactions", "assessment_attempts", "discussion_actions"]
        max_values = {dim: max((metrics[dim] for metrics in per_learner.values()), default=0.0) for dim in dimensions}

        score_by_learner: dict[str, float] = {}
        for learner_id, metrics in per_learner.items():
            score = (
                0.35 * (metrics["active_minutes"] / max_values["active_minutes"] if max_values["active_minutes"] else 0)
                + 0.25
                * (metrics["content_interactions"] / max_values["content_interactions"] if max_values["content_interactions"] else 0)
                + 0.20
                * (metrics["assessment_attempts"] / max_values["assessment_attempts"] if max_values["assessment_attempts"] else 0)
                + 0.20 * (metrics["discussion_actions"] / max_values["discussion_actions"] if max_values["discussion_actions"] else 0)
            )
            score_by_learner[learner_id] = round(score * 100, 2)

        scores = sorted(score_by_learner.values())
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        p90_index = int(len(scores) * 0.9) - 1 if scores else 0

        return {
            "course_id": course_id,
            "cohort_id": cohort_id,
            "active_learners": len(per_learner),
            "average_engagement_score": avg_score,
            "engagement_score_distribution": {
                "p50": scores[len(scores) // 2] if scores else 0.0,
                "p90": scores[max(0, p90_index)] if scores else 0.0,
            },
            "scores_by_learner": score_by_learner,
        }

    def cohort_performance_metrics(
        self,
        cohort_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> dict:
        cohort_courses = {row.course_id for row in self.repository.enrollments if row.cohort_id == cohort_id}
        course_completion = {
            course_id: self.course_completion_analytics(course_id, start_at=start_at, end_at=end_at, cohort_id=cohort_id)
            for course_id in cohort_courses
        }

        course_engagement = {
            course_id: self.learner_engagement_metrics(course_id, start_at=start_at, end_at=end_at, cohort_id=cohort_id)
            for course_id in cohort_courses
        }

        attempts = self.repository.list_assessment_attempts(cohort_id, start_at, end_at)
        avg_assessment_score = round(sum((a.score / a.max_score) * 100 for a in attempts) / len(attempts), 2) if attempts else 0.0

        completion_rates = [row["completion_rate"] for row in course_completion.values()]
        engagement_scores = [row["average_engagement_score"] for row in course_engagement.values()]

        return {
            "cohort_id": cohort_id,
            "tracked_courses": len(cohort_courses),
            "average_completion_rate": round(sum(completion_rates) / len(completion_rates), 2) if completion_rates else 0.0,
            "average_engagement_score": round(sum(engagement_scores) / len(engagement_scores), 2) if engagement_scores else 0.0,
            "average_assessment_score": avg_assessment_score,
            "course_breakdown": {
                course_id: {
                    "completion_rate": course_completion[course_id]["completion_rate"],
                    "engagement_score": course_engagement[course_id]["average_engagement_score"],
                }
                for course_id in cohort_courses
            },
        }

    def learning_path_completion_analysis(
        self,
        learning_path_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> dict:
        snapshots = self.repository.list_path_snapshots(learning_path_id, start_at, end_at, cohort_id)
        latest_by_learner = {}
        for row in sorted(snapshots, key=lambda x: x.snapshot_timestamp):
            latest_by_learner[row.learner_id] = row

        learners = list(latest_by_learner.values())
        completed = [row for row in learners if row.progress_percent >= 100 or row.completed_modules >= row.total_modules]

        stage_counts = {
            "assigned": len(learners),
            "started": len([row for row in learners if row.progress_percent > 0]),
            "midpoint": len([row for row in learners if row.progress_percent >= 50]),
            "completed": len(completed),
        }

        drop_off = {}
        funnel = ["assigned", "started", "midpoint", "completed"]
        for idx, stage in enumerate(funnel[:-1]):
            next_stage = funnel[idx + 1]
            drop_off[stage] = self._safe_rate(stage_counts[stage] - stage_counts[next_stage], stage_counts[stage])

        dominant_stage = max(drop_off, key=drop_off.get) if drop_off else None

        return {
            "learning_path_id": learning_path_id,
            "cohort_id": cohort_id,
            "assigned_learners": stage_counts["assigned"],
            "completed_learners": stage_counts["completed"],
            "completion_rate": self._safe_rate(stage_counts["completed"], stage_counts["assigned"]),
            "stage_counts": stage_counts,
            "drop_off_rate_by_stage": drop_off,
            "dominant_drop_off_stage": dominant_stage,
        }
