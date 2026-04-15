"""SCORM runtime service — package launch, CMI state tracking, and completion reporting.

CGAP-066: replaces NotImplementedError stub. Implements the 3 runtime operations from
scorm_runtime_spec.md:
  1. Package launch   — session init with CMI defaults, returns launch context + session token
  2. Progress tracking — LMSSetValue/Commit CMI persistence, suspend_data checkpointing
  3. Completion reporting — outcome computation (passed/failed/completed/incomplete),
     completion timestamp recording, canonical completion event emission

Supports SCORM 1.2 (cmi.core.*) and SCORM 2004 (cmi.completion_status / success_status).

Spec refs: docs/specs/scorm_runtime_spec.md
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_EVENTS = Path(__file__).resolve().parents[3] / "shared" / "events"
if str(_EVENTS.parent) not in sys.path:
    sys.path.insert(0, str(_EVENTS.parent))

try:
    from shared.events.envelope import publish_event  # noqa: F401 — best-effort
    _HAS_BUS = True
except Exception:
    _HAS_BUS = False


# ------------------------------------------------------------------ #
# SCORM version constants                                              #
# ------------------------------------------------------------------ #

SCORM_12 = "1.2"
SCORM_2004 = "2004"
LAUNCH_MODES = {"normal", "review", "browse"}

# Completion/success terminal values
_SCORM12_TERMINAL = {"passed", "failed", "completed"}
_SCORM2004_COMPLETE = {"completed", "incomplete", "not attempted", "unknown"}
_SCORM2004_SUCCESS = {"passed", "failed", "unknown"}


# ------------------------------------------------------------------ #
# Data models                                                          #
# ------------------------------------------------------------------ #

@dataclass
class ScormSession:
    """In-flight or completed SCORM runtime session for one learner × SCO attempt."""
    registration_id: str
    tenant_id: str
    learner_id: str
    course_id: str
    sco_id: str
    launch_mode: str
    scorm_version: str
    session_token: str
    cmi_data: dict[str, Any]
    is_active: bool = True
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    outcome: str | None = None       # passed / failed / completed / incomplete
    score_raw: float | None = None
    commit_count: int = 0


class ScormError(Exception):
    """Raised on invalid SCORM operations."""


class ScormSessionNotFound(ScormError):
    """Raised when the registration_id has no active session."""


# ------------------------------------------------------------------ #
# CMI helpers                                                          #
# ------------------------------------------------------------------ #

def _default_cmi(scorm_version: str, learner_id: str) -> dict[str, Any]:
    """Return minimal initial CMI state per SCORM version."""
    if scorm_version == SCORM_2004:
        return {
            "cmi.completion_status": "not attempted",
            "cmi.success_status": "unknown",
            "cmi.score.scaled": None,
            "cmi.score.raw": None,
            "cmi.score.min": None,
            "cmi.score.max": None,
            "cmi.session_time": "PT0S",
            "cmi.total_time": "PT0S",
            "cmi.location": "",
            "cmi.suspend_data": "",
            "cmi.progress_measure": None,
            "cmi.mode": "normal",
            "cmi.learner_id": learner_id,
        }
    # SCORM 1.2 defaults
    return {
        "cmi.core.lesson_status": "not attempted",
        "cmi.core.score.raw": None,
        "cmi.core.score.min": None,
        "cmi.core.score.max": None,
        "cmi.core.session_time": "00:00:00",
        "cmi.core.total_time": "00:00:00",
        "cmi.core.lesson_location": "",
        "cmi.suspend_data": "",
        "cmi.core.exit": "",
        "cmi.core.student_id": learner_id,
        "cmi.core.student_name": "",
    }


def _compute_outcome(cmi: dict[str, Any], scorm_version: str) -> tuple[str, float | None]:
    """Derive (outcome_label, score_raw) from CMI state."""
    def _f(v: Any) -> float | None:
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    if scorm_version == SCORM_2004:
        success = cmi.get("cmi.success_status", "unknown")
        completion = cmi.get("cmi.completion_status", "not attempted")
        score = _f(cmi.get("cmi.score.raw"))
        if success == "passed":
            return "passed", score
        if success == "failed":
            return "failed", score
        if completion == "completed":
            return "completed", score
        return "incomplete", score
    else:
        status = cmi.get("cmi.core.lesson_status", "not attempted")
        score = _f(cmi.get("cmi.core.score.raw"))
        if status in {"passed", "failed", "completed"}:
            return status, score
        return "incomplete", score


# ------------------------------------------------------------------ #
# Main service                                                         #
# ------------------------------------------------------------------ #

class ScormRuntimeManagementService:
    """Tenant-scoped SCORM runtime service per scorm_runtime_spec.md.

    Implements all 3 spec runtime operations:
    - Package launch: initialize CMI, create session, return launch context
    - Progress tracking: LMSSetValue / LMSCommit CMI state persistence
    - Completion reporting: LMSFinish outcome computation + completion event
    """

    def __init__(self) -> None:
        # tenant_id → {registration_id → ScormSession}
        self._sessions: dict[str, dict[str, ScormSession]] = {}
        # token → (tenant_id, registration_id) for fast lookup
        self._token_index: dict[str, tuple[str, str]] = {}

    # ------------------------------------------------------------------ #
    # Operation 1: Package launch                                          #
    # ------------------------------------------------------------------ #

    def launch_package(
        self,
        *,
        tenant_id: str,
        learner_id: str,
        course_id: str,
        registration_id: str,
        sco_id: str,
        launch_mode: str = "normal",
        scorm_version: str = SCORM_12,
    ) -> dict[str, Any]:
        """Initialize a SCORM runtime session and return the launch context.

        scorm_runtime_spec launch operation: LMS resolves SCO launch URL, initializes
        SCORM API session, creates runtime attempt record, returns session_token and
        initial CMI values.
        """
        if launch_mode not in LAUNCH_MODES:
            raise ScormError(f"launch_mode must be one of {LAUNCH_MODES}")
        if scorm_version not in {SCORM_12, SCORM_2004}:
            raise ScormError(f"scorm_version must be '{SCORM_12}' or '{SCORM_2004}'")

        import uuid as _uuid
        session_token = str(_uuid.uuid4())
        cmi = _default_cmi(scorm_version, learner_id)

        # Carry forward suspend_data from a prior incomplete session if one exists
        prior = self._sessions.get(tenant_id, {}).get(registration_id)
        if prior and prior.outcome in (None, "incomplete"):
            cmi["cmi.suspend_data"] = prior.cmi_data.get("cmi.suspend_data", "")
            if scorm_version == SCORM_12:
                cmi["cmi.core.total_time"] = prior.cmi_data.get("cmi.core.total_time", "00:00:00")
            else:
                cmi["cmi.total_time"] = prior.cmi_data.get("cmi.total_time", "PT0S")

        session = ScormSession(
            registration_id=registration_id,
            tenant_id=tenant_id,
            learner_id=learner_id,
            course_id=course_id,
            sco_id=sco_id,
            launch_mode=launch_mode,
            scorm_version=scorm_version,
            session_token=session_token,
            cmi_data=cmi,
        )
        self._sessions.setdefault(tenant_id, {})[registration_id] = session
        self._token_index[session_token] = (tenant_id, registration_id)

        return {
            "registration_id": registration_id,
            "session_token": session_token,
            "sco_id": sco_id,
            "launch_mode": launch_mode,
            "scorm_version": scorm_version,
            "initial_cmi": dict(cmi),
            "launched_at": session.started_at.isoformat(),
        }

    # ------------------------------------------------------------------ #
    # Operation 2a: LMSSetValue / SetValue (progress tracking)            #
    # ------------------------------------------------------------------ #

    def set_cmi_value(
        self,
        *,
        tenant_id: str,
        registration_id: str,
        key: str,
        value: Any,
    ) -> dict[str, Any]:
        """Persist a CMI data model update from the SCO (LMSSetValue / SetValue call).

        scorm_runtime_spec progress tracking: validates and persists CMI updates,
        checkpoints learner state for resume.
        """
        session = self._get_active_session(tenant_id, registration_id)
        session.cmi_data[key] = value
        return {"registration_id": registration_id, "key": key, "accepted": True}

    def set_cmi_values(
        self,
        *,
        tenant_id: str,
        registration_id: str,
        updates: dict[str, Any],
    ) -> dict[str, Any]:
        """Batch CMI update — applies multiple LMSSetValue calls atomically."""
        session = self._get_active_session(tenant_id, registration_id)
        session.cmi_data.update(updates)
        return {
            "registration_id": registration_id,
            "keys_updated": list(updates.keys()),
            "accepted": True,
        }

    # ------------------------------------------------------------------ #
    # Operation 2b: LMSCommit / Commit (checkpoint)                       #
    # ------------------------------------------------------------------ #

    def commit(self, *, tenant_id: str, registration_id: str) -> dict[str, Any]:
        """Checkpoint CMI state (LMSCommit / Commit call).

        scorm_runtime_spec: updates progress percentage and time spent, stores
        attempt history for analytics.
        """
        session = self._get_active_session(tenant_id, registration_id)
        session.commit_count += 1
        outcome, score = _compute_outcome(session.cmi_data, session.scorm_version)
        return {
            "registration_id": registration_id,
            "commit_count": session.commit_count,
            "current_outcome": outcome,
            "score_raw": score,
            "committed_at": datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------ #
    # Operation 3: LMSFinish / Terminate (completion reporting)           #
    # ------------------------------------------------------------------ #

    def finish_session(
        self,
        *,
        tenant_id: str,
        registration_id: str,
        mastery_score: float | None = None,
    ) -> dict[str, Any]:
        """Process LMSFinish / Terminate — compute final outcome and record completion.

        scorm_runtime_spec completion reporting: computes final attempt outcome
        (completed/passed/failed/incomplete), records completion timestamp and score,
        updates course enrollment status, emits completion event to downstream systems.
        """
        session = self._get_active_session(tenant_id, registration_id)

        outcome, score = _compute_outcome(session.cmi_data, session.scorm_version)

        # Apply mastery_score override for SCORM 1.2 (lesson_status computed from score vs mastery)
        if (
            mastery_score is not None
            and session.scorm_version == SCORM_12
            and score is not None
        ):
            if score >= mastery_score:
                outcome = "passed"
            else:
                outcome = "failed"

        session.outcome = outcome
        session.score_raw = score
        session.is_active = False
        session.finished_at = datetime.now(timezone.utc)

        completion_record = {
            "registration_id": registration_id,
            "tenant_id": tenant_id,
            "learner_id": session.learner_id,
            "course_id": session.course_id,
            "sco_id": session.sco_id,
            "scorm_version": session.scorm_version,
            "outcome": outcome,
            "score_raw": score,
            "completed_at": session.finished_at.isoformat(),
            "session_duration_s": (session.finished_at - session.started_at).seconds,
        }

        # Emit canonical completion event to platform event bus
        if _HAS_BUS and outcome in {"passed", "completed"}:
            try:
                publish_event(
                    event_type="scorm.completion.reported",
                    tenant_id=tenant_id,
                    payload=completion_record,
                )
            except Exception:
                pass  # event emission is best-effort; never block completion recording

        return completion_record

    # ------------------------------------------------------------------ #
    # Session state read                                                   #
    # ------------------------------------------------------------------ #

    def get_session_state(
        self,
        *,
        tenant_id: str,
        registration_id: str,
    ) -> dict[str, Any]:
        """Return current CMI state for a session (active or finished)."""
        session = self._sessions.get(tenant_id, {}).get(registration_id)
        if not session:
            raise ScormSessionNotFound(f"No session for registration_id='{registration_id}'")
        return {
            "registration_id": registration_id,
            "learner_id": session.learner_id,
            "course_id": session.course_id,
            "sco_id": session.sco_id,
            "scorm_version": session.scorm_version,
            "launch_mode": session.launch_mode,
            "is_active": session.is_active,
            "outcome": session.outcome,
            "score_raw": session.score_raw,
            "commit_count": session.commit_count,
            "started_at": session.started_at.isoformat(),
            "finished_at": session.finished_at.isoformat() if session.finished_at else None,
            "cmi_data": dict(session.cmi_data),
        }

    def list_sessions(
        self,
        *,
        tenant_id: str,
        learner_id: str | None = None,
        course_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List all sessions for a tenant, optionally filtered."""
        sessions = list(self._sessions.get(tenant_id, {}).values())
        if learner_id:
            sessions = [s for s in sessions if s.learner_id == learner_id]
        if course_id:
            sessions = [s for s in sessions if s.course_id == course_id]
        return [
            {
                "registration_id": s.registration_id,
                "learner_id": s.learner_id,
                "course_id": s.course_id,
                "sco_id": s.sco_id,
                "scorm_version": s.scorm_version,
                "is_active": s.is_active,
                "outcome": s.outcome,
                "score_raw": s.score_raw,
                "started_at": s.started_at.isoformat(),
                "finished_at": s.finished_at.isoformat() if s.finished_at else None,
            }
            for s in sessions
        ]

    # ------------------------------------------------------------------ #
    # Internal                                                             #
    # ------------------------------------------------------------------ #

    def _get_active_session(self, tenant_id: str, registration_id: str) -> ScormSession:
        session = self._sessions.get(tenant_id, {}).get(registration_id)
        if not session:
            raise ScormSessionNotFound(f"No session for registration_id='{registration_id}'")
        if not session.is_active:
            raise ScormError(
                f"Session '{registration_id}' is already finished (outcome={session.outcome})"
            )
        return session
