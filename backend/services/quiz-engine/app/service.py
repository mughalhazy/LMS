"""Thin adapter around the quiz engine domain service."""

from __future__ import annotations

from src.quiz_engine import QuizEngine


class Service(QuizEngine):
    """Backward-compatible app-layer alias for the quiz engine."""

