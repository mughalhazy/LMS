"""Canonical navigation rules for lesson-service navigation module."""

NAVIGATION_RULES = {
    "next_lesson_navigation": {
        "description": "Advance to the nearest published lesson with higher order_index.",
        "behavior": [
            "Skip draft lessons.",
            "Return None at course end.",
            "If target lesson is locked, return reason=target_locked.",
        ],
    },
    "previous_lesson_navigation": {
        "description": "Move to the nearest published lesson with lower order_index.",
        "behavior": [
            "Skip draft lessons.",
            "Return None at first published lesson.",
        ],
    },
    "lesson_completion_triggers": {
        "description": "Mark completion when configured policy is satisfied.",
        "policies": {
            "view": "completion event with viewed=True",
            "quiz_pass": "completion event with score >= minimum_passing_score",
            "manual": "completion event with manually_completed=True",
        },
    },
    "lesson_locking_rules": {
        "description": "Determine whether learner can open lesson.",
        "modes": {
            "none": "All published lessons unlocked.",
            "sequential": "All prior published lessons must be completed.",
            "prerequisite": "Explicit prerequisite_lesson_ids must be completed.",
        },
    },
}
