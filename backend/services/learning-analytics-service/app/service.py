from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from typing import Any

from .repository import AnalyticsRepository


class LearningAnalyticsService:
    def __init__(self, repository: AnalyticsRepository) -> None:
        self.repository = repository

    @staticmethod
    def _safe_rate(numerator: float, denominator: float) -> float:
        if denominator <= 0:
            return 0.0
        return round((numerator / denominator) * 100, 2)

    @staticmethod
    def _round(value: float) -> float:
        return round(value, 2)

    @staticmethod
    def _sentiment_label(score: float) -> str:
        if score >= 0.25:
            return "positive"
        if score <= -0.25:
            return "negative"
        return "neutral"

    def ingest_events(self, events: list[dict[str, Any]]) -> dict[str, int | float]:
        result = self.repository.ingest_events(events)
        total = result["processed"] + result["rejected"]
        success_rate = self._safe_rate(result["processed"], total)
        return {
            "processed": result["processed"],
            "rejected": result["rejected"],
            "success_rate": success_rate,
        }

    def course_completion_analytics(
        self,
        tenant_id: str,
        course_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> dict:
        enrolled = [
            row
            for row in self.repository.list_enrollments(tenant_id, course_id, cohort_id)
            if row.enrollment_status in {"enrolled", "in_progress"}
        ]
        completion_rows = [
            row
            for row in self.repository.list_completions(tenant_id, course_id, start_at, end_at, cohort_id)
            if row.completion_status == "completed"
        ]
        completed_learner_ids = {row.learner_id for row in completion_rows}
        median_time_hours = 0.0
        if completion_rows:
            hours = sorted([row.total_time_spent_seconds / 3600 for row in completion_rows])
            mid = len(hours) // 2
            median_time_hours = round((hours[mid] if len(hours) % 2 else (hours[mid - 1] + hours[mid]) / 2), 2)

        return {
            "tenant_id": tenant_id,
            "course_id": course_id,
            "cohort_id": cohort_id,
            "enrolled_learners": len({item.learner_id for item in enrolled}),
            "completed_learners": len(completed_learner_ids),
            "completion_rate": self._safe_rate(len(completed_learner_ids), len({item.learner_id for item in enrolled})),
            "median_time_to_complete_hours": median_time_hours,
        }

    def learner_engagement_metrics(
        self,
        tenant_id: str,
        course_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> dict:
        events = self.repository.list_activities(tenant_id, course_id, start_at, end_at, cohort_id)
        per_learner: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
        sentiment_totals: dict[str, float] = defaultdict(float)
        sentiment_counts: dict[str, int] = defaultdict(int)

        for row in events:
            per_learner[row.learner_id]["active_minutes"] += row.active_minutes
            per_learner[row.learner_id]["content_interactions"] += row.content_interactions
            per_learner[row.learner_id]["assessment_attempts"] += row.assessment_attempts
            per_learner[row.learner_id]["discussion_actions"] += row.discussion_actions
            sentiment_totals[row.learner_id] += row.sentiment_score
            sentiment_counts[row.learner_id] += 1

        dimensions = ["active_minutes", "content_interactions", "assessment_attempts", "discussion_actions"]
        max_values = {dim: max((metrics[dim] for metrics in per_learner.values()), default=0.0) for dim in dimensions}

        score_by_learner: dict[str, float] = {}
        sentiment_by_learner: dict[str, dict[str, float | str]] = {}
        sentiment_distribution = {"positive": 0, "neutral": 0, "negative": 0}
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

            avg_sentiment = sentiment_totals[learner_id] / sentiment_counts[learner_id] if sentiment_counts[learner_id] else 0.0
            label = self._sentiment_label(avg_sentiment)
            sentiment_distribution[label] += 1
            sentiment_by_learner[learner_id] = {
                "average_sentiment": self._round(avg_sentiment),
                "label": label,
            }

        scores = sorted(score_by_learner.values())
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        p90_index = int(len(scores) * 0.9) - 1 if scores else 0
        average_sentiment = self._round(sum(sentiment_totals.values()) / sum(sentiment_counts.values())) if sentiment_counts else 0.0

        return {
            "tenant_id": tenant_id,
            "course_id": course_id,
            "cohort_id": cohort_id,
            "active_learners": len(per_learner),
            "average_engagement_score": avg_score,
            "engagement_score_distribution": {
                "p50": scores[len(scores) // 2] if scores else 0.0,
                "p90": scores[max(0, p90_index)] if scores else 0.0,
            },
            "scores_by_learner": score_by_learner,
            "average_sentiment": average_sentiment,
            "sentiment_distribution": sentiment_distribution,
            "sentiment_by_learner": sentiment_by_learner,
        }

    def engagement_trends(
        self,
        tenant_id: str,
        course_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> dict:
        events = self.repository.list_activities(tenant_id, course_id, start_at, end_at, cohort_id)
        grouped: dict[str, list] = defaultdict(list)
        for row in events:
            grouped[row.event_timestamp.date().isoformat()].append(row)

        trend_points = []
        previous_score: float | None = None
        for period in sorted(grouped):
            rows = grouped[period]
            active_minutes = sum(row.active_minutes for row in rows)
            interactions = sum(
                row.content_interactions + row.assessment_attempts + row.discussion_actions for row in rows
            )
            avg_sentiment = sum(row.sentiment_score for row in rows) / len(rows)
            engagement_score = self._round((0.6 * active_minutes) + (4.0 * interactions))
            trend_points.append(
                {
                    "period": period,
                    "engagement_score": engagement_score,
                    "active_minutes": self._round(active_minutes),
                    "interaction_count": interactions,
                    "average_sentiment": self._round(avg_sentiment),
                    "sentiment_label": self._sentiment_label(avg_sentiment),
                    "engagement_delta": self._round(engagement_score - previous_score) if previous_score is not None else 0.0,
                }
            )
            previous_score = engagement_score

        overall_delta = self._round(trend_points[-1]["engagement_score"] - trend_points[0]["engagement_score"]) if len(trend_points) > 1 else 0.0
        if overall_delta > 5:
            direction = "up"
        elif overall_delta < -5:
            direction = "down"
        else:
            direction = "stable"

        return {
            "tenant_id": tenant_id,
            "course_id": course_id,
            "cohort_id": cohort_id,
            "periods": len(trend_points),
            "direction": direction,
            "net_engagement_delta": overall_delta,
            "trend_points": trend_points,
        }

    def engagement_dashboard(
        self,
        tenant_id: str,
        course_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> dict:
        completion = self.course_completion_analytics(tenant_id, course_id, start_at, end_at, cohort_id)
        engagement = self.learner_engagement_metrics(tenant_id, course_id, start_at, end_at, cohort_id)
        trends = self.engagement_trends(tenant_id, course_id, start_at, end_at, cohort_id)

        latest_trend = trends["trend_points"][-1] if trends["trend_points"] else None
        widgets = [
            {
                "widget_id": "engagement_overview",
                "widget_name": "Engagement Overview",
                "metrics": [
                    {"metric": "active_learners", "value": float(engagement["active_learners"]), "unit": "learners"},
                    {"metric": "average_engagement_score", "value": engagement["average_engagement_score"], "unit": "score"},
                    {"metric": "completion_rate", "value": completion["completion_rate"], "unit": "percent"},
                ],
            },
            {
                "widget_id": "sentiment_tracking",
                "widget_name": "Sentiment Tracking",
                "metrics": [
                    {"metric": "average_sentiment", "value": engagement["average_sentiment"], "unit": "score"},
                    {"metric": "positive_learners", "value": float(engagement["sentiment_distribution"]["positive"]), "unit": "learners"},
                    {"metric": "negative_learners", "value": float(engagement["sentiment_distribution"]["negative"]), "unit": "learners"},
                ],
            },
            {
                "widget_id": "engagement_trends",
                "widget_name": "Engagement Trends",
                "metrics": [
                    {"metric": "net_engagement_delta", "value": trends["net_engagement_delta"], "unit": "score"},
                    {"metric": "tracked_periods", "value": float(trends["periods"]), "unit": "days"},
                    {"metric": "latest_sentiment", "value": latest_trend["average_sentiment"] if latest_trend else 0.0, "unit": "score"},
                ],
                "direction": trends["direction"],
                "trend_points": trends["trend_points"],
            },
        ]

        return {
            "tenant_id": tenant_id,
            "course_id": course_id,
            "cohort_id": cohort_id,
            "widgets": widgets,
            "summary": {
                "completion_rate": completion["completion_rate"],
                "average_engagement_score": engagement["average_engagement_score"],
                "average_sentiment": engagement["average_sentiment"],
                "trend_direction": trends["direction"],
            },
        }

    def cohort_performance_metrics(
        self,
        tenant_id: str,
        cohort_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
    ) -> dict:
        cohort_courses = {
            row.course_id
            for row in self.repository.enrollments
            if row.tenant_id == tenant_id and row.cohort_id == cohort_id
        }
        course_completion = {
            course_id: self.course_completion_analytics(tenant_id, course_id, start_at=start_at, end_at=end_at, cohort_id=cohort_id)
            for course_id in cohort_courses
        }

        course_engagement = {
            course_id: self.learner_engagement_metrics(tenant_id, course_id, start_at=start_at, end_at=end_at, cohort_id=cohort_id)
            for course_id in cohort_courses
        }

        attempts = self.repository.list_assessment_attempts(tenant_id, cohort_id, start_at, end_at)
        avg_assessment_score = round(sum((a.score / a.max_score) * 100 for a in attempts) / len(attempts), 2) if attempts else 0.0

        completion_rates = [row["completion_rate"] for row in course_completion.values()]
        engagement_scores = [row["average_engagement_score"] for row in course_engagement.values()]
        sentiment_scores = [row["average_sentiment"] for row in course_engagement.values()]

        return {
            "tenant_id": tenant_id,
            "cohort_id": cohort_id,
            "tracked_courses": len(cohort_courses),
            "average_completion_rate": round(sum(completion_rates) / len(completion_rates), 2) if completion_rates else 0.0,
            "average_engagement_score": round(sum(engagement_scores) / len(engagement_scores), 2) if engagement_scores else 0.0,
            "average_assessment_score": avg_assessment_score,
            "average_sentiment": round(sum(sentiment_scores) / len(sentiment_scores), 2) if sentiment_scores else 0.0,
            "course_breakdown": {
                course_id: {
                    "completion_rate": course_completion[course_id]["completion_rate"],
                    "engagement_score": course_engagement[course_id]["average_engagement_score"],
                    "average_sentiment": course_engagement[course_id]["average_sentiment"],
                }
                for course_id in cohort_courses
            },
        }

    def learning_and_performance_metrics(
        self,
        tenant_id: str,
        course_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> dict:
        completion = self.course_completion_analytics(tenant_id, course_id, start_at, end_at, cohort_id)
        engagement = self.learner_engagement_metrics(tenant_id, course_id, start_at, end_at, cohort_id)
        attempts = self.repository.list_assessment_attempts(tenant_id, cohort_id or "", start_at, end_at) if cohort_id else [
            row
            for row in self.repository.assessment_attempts
            if row.tenant_id == tenant_id
            and row.course_id == course_id
            and self.repository._in_window(row.submitted_at, start_at, end_at)
        ]

        performance_by_learner: dict[str, dict[str, float]] = defaultdict(lambda: {"score_sum": 0.0, "attempts": 0.0})
        for attempt in attempts:
            score_percent = (attempt.score / attempt.max_score) * 100 if attempt.max_score else 0.0
            performance_by_learner[attempt.learner_id]["score_sum"] += score_percent
            performance_by_learner[attempt.learner_id]["attempts"] += 1

        learner_performance = {
            learner_id: self._round(values["score_sum"] / values["attempts"])
            for learner_id, values in performance_by_learner.items()
            if values["attempts"] > 0
        }
        avg_performance = self._round(sum(learner_performance.values()) / len(learner_performance)) if learner_performance else 0.0

        return {
            "tenant_id": tenant_id,
            "course_id": course_id,
            "cohort_id": cohort_id,
            "learning_metrics": {
                "completion_rate": completion["completion_rate"],
                "active_learners": engagement["active_learners"],
                "average_engagement_score": engagement["average_engagement_score"],
                "average_sentiment": engagement["average_sentiment"],
            },
            "performance_metrics": {
                "average_assessment_score": avg_performance,
                "assessed_learners": len(learner_performance),
                "learner_performance": learner_performance,
            },
        }

    def learning_path_completion_analysis(
        self,
        tenant_id: str,
        learning_path_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> dict:
        snapshots = self.repository.list_path_snapshots(tenant_id, learning_path_id, start_at, end_at, cohort_id)
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
            "tenant_id": tenant_id,
            "learning_path_id": learning_path_id,
            "cohort_id": cohort_id,
            "assigned_learners": stage_counts["assigned"],
            "completed_learners": stage_counts["completed"],
            "completion_rate": self._safe_rate(stage_counts["completed"], stage_counts["assigned"]),
            "stage_counts": stage_counts,
            "drop_off_rate_by_stage": drop_off,
            "dominant_drop_off_stage": dominant_stage,
        }

    def ai_service_signals(
        self,
        tenant_id: str,
        course_id: str,
        start_at: datetime | None = None,
        end_at: datetime | None = None,
        cohort_id: str | None = None,
    ) -> dict:
        aggregated = self.learning_and_performance_metrics(tenant_id, course_id, start_at, end_at, cohort_id)
        completion = self.course_completion_analytics(tenant_id, course_id, start_at, end_at, cohort_id)
        engagement = self.learner_engagement_metrics(tenant_id, course_id, start_at, end_at, cohort_id)
        trends = self.engagement_trends(tenant_id, course_id, start_at, end_at, cohort_id)

        at_risk = [
            learner_id
            for learner_id, score in engagement["scores_by_learner"].items()
            if score < 40 or engagement["sentiment_by_learner"].get(learner_id, {}).get("label") == "negative"
        ]

        return {
            "tenant_id": tenant_id,
            "course_id": course_id,
            "cohort_id": cohort_id,
            "learning_metrics": aggregated["learning_metrics"],
            "performance_metrics": aggregated["performance_metrics"],
            "completion_rate": completion["completion_rate"],
            "active_learners": engagement["active_learners"],
            "trend_direction": trends["direction"],
            "average_sentiment": engagement["average_sentiment"],
            "at_risk_learners": at_risk,
            "tutor_signal": {
                "needs_intervention": bool(at_risk or completion["completion_rate"] < 60),
                "suggested_focus": "course-recap" if completion["completion_rate"] < 60 else "practice-coaching",
            },
            "recommendation_signal": {
                "dropoff_rate": round(max(0.0, 1 - (completion["completion_rate"] / 100)), 2),
                "engagement_band": "low" if engagement["average_engagement_score"] < 40 else "medium" if engagement["average_engagement_score"] < 70 else "high",
            },
        }
