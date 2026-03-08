"""State schema/types, constants, and validation helpers."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from desloppify.base.discovery.paths import get_project_root
from desloppify.base.enums import Status, canonical_issue_status, issue_status_tokens
from desloppify.engine._state.schema_scores import (
    json_default,
)
from desloppify.engine._state.schema_types import (
    AssessmentImportAuditEntry,
    AttestationLogEntry,
    ConcernDismissal,
    DimensionScore,
    IgnoreIntegrityModel,
    Issue,
    LangCapability,
    ReviewCacheModel,
    ScanDiff,
    ScanHistoryEntry,
    ScoreConfidenceDetector,
    ScoreConfidenceModel,
    StateModel,
    StateStats,
    SubjectiveAssessment,
    SubjectiveAssessmentJudgment,
    SubjectiveIntegrity,
    TierStats,
)

__all__ = [
    "ConcernDismissal",
    "AssessmentImportAuditEntry",
    "AttestationLogEntry",
    "Issue",
    "TierStats",
    "StateStats",
    "DimensionScore",
    "ScoreConfidenceDetector",
    "ScoreConfidenceModel",
    "ScanHistoryEntry",
    "SubjectiveAssessment",
    "SubjectiveAssessmentJudgment",
    "SubjectiveIntegrity",
    "LangCapability",
    "ReviewCacheModel",
    "IgnoreIntegrityModel",
    "StateModel",
    "ScanDiff",
    "get_state_dir",
    "get_state_file",
    "CURRENT_VERSION",
    "utc_now",
    "empty_state",
    "ensure_state_defaults",
    "validate_state_invariants",
    "json_default",
    "migrate_state_keys",
]

_ALLOWED_ISSUE_STATUSES: set[str] = {
    *issue_status_tokens(),
}


def get_state_dir() -> Path:
    """Return the active state directory for the current runtime context."""
    return get_project_root() / ".desloppify"


def get_state_file() -> Path:
    """Return the default state file for the current runtime context."""
    return get_state_dir() / "state.json"


CURRENT_VERSION = 1


def utc_now() -> str:
    """Return current UTC timestamp with second-level precision."""
    return datetime.now(UTC).isoformat(timespec="seconds")


def empty_state() -> StateModel:
    """Return a new empty state payload."""
    return {
        "version": CURRENT_VERSION,
        "created": utc_now(),
        "last_scan": None,
        "scan_count": 0,
        "overall_score": 0,
        "objective_score": 0,
        "strict_score": 0,
        "verified_strict_score": 0,
        "stats": {},
        "issues": {},
        "scan_coverage": {},
        "score_confidence": {},
        "subjective_integrity": {},
        "subjective_assessments": {},
    }


def _as_non_negative_int(value: Any, default: int = 0) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else 0


def _rename_key(d: dict, old: str, new: str) -> bool:
    if old not in d:
        return False
    d.setdefault(new, d.pop(old))
    return True


def migrate_state_keys(state: StateModel | dict[str, Any]) -> None:
    """Migrate legacy key names in-place.

    - ``"findings"`` → ``"issues"``
    - ``dimension_scores[dim]["issues"]`` → ``"failing"``
    """
    state_dict = cast(dict[str, Any], state)
    _rename_key(state_dict, "findings", "issues")

    for ds in state_dict.get("dimension_scores", {}).values():
        if isinstance(ds, dict):
            _rename_key(ds, "issues", "failing")

    for entry in state_dict.get("scan_history", []):
        if not isinstance(entry, dict):
            continue
        _rename_key(entry, "raw_findings", "raw_issues")
        for ds in (entry.get("dimension_scores") or {}).values():
            if isinstance(ds, dict):
                _rename_key(ds, "issues", "failing")


def ensure_state_defaults(state: StateModel | dict) -> None:
    """Normalize loose/legacy state payloads to a valid base shape in-place."""
    migrate_state_keys(state)

    mutable_state = cast(dict[str, Any], state)
    for key, value in empty_state().items():
        mutable_state.setdefault(key, value)

    if not isinstance(state.get("issues"), dict):
        state["issues"] = {}
    if not isinstance(state.get("stats"), dict):
        state["stats"] = {}
    if not isinstance(state.get("scan_history"), list):
        state["scan_history"] = []
    if not isinstance(state.get("scan_coverage"), dict):
        state["scan_coverage"] = {}
    if not isinstance(state.get("score_confidence"), dict):
        state["score_confidence"] = {}
    if not isinstance(state.get("subjective_integrity"), dict):
        state["subjective_integrity"] = {}

    all_issues = state["issues"]
    to_remove: list[str] = []
    for issue_id, issue in all_issues.items():
        if not isinstance(issue, dict):
            to_remove.append(issue_id)
            continue

        issue.setdefault("id", issue_id)
        issue.setdefault("detector", "unknown")
        issue.setdefault("file", "")
        issue.setdefault("tier", 3)
        issue.setdefault("confidence", "low")
        issue.setdefault("summary", "")
        issue.setdefault("detail", {})
        issue.setdefault("status", Status.OPEN)
        issue["status"] = canonical_issue_status(
            issue.get("status"),
            default=Status.OPEN,
        )
        issue.setdefault("note", None)
        issue.setdefault("first_seen", state.get("created") or utc_now())
        issue.setdefault("last_seen", issue["first_seen"])
        issue.setdefault("resolved_at", None)
        issue["reopen_count"] = _as_non_negative_int(
            issue.get("reopen_count", 0), default=0
        )
        issue.setdefault("suppressed", False)
        issue.setdefault("suppressed_at", None)
        issue.setdefault("suppression_pattern", None)

    for issue_id in to_remove:
        all_issues.pop(issue_id, None)

    for entry in state["scan_history"]:
        if not isinstance(entry, dict):
            continue
        integrity = entry.get("subjective_integrity")
        if integrity is not None and not isinstance(integrity, dict):
            entry["subjective_integrity"] = None

    state["scan_count"] = _as_non_negative_int(state.get("scan_count", 0), default=0)
    return None


def validate_state_invariants(state: StateModel) -> None:
    """Raise ValueError when core state invariants are violated."""
    if not isinstance(state.get("issues"), dict):
        raise ValueError("state.issues must be a dict")
    if not isinstance(state.get("stats"), dict):
        raise ValueError("state.stats must be a dict")

    all_issues = state["issues"]
    for issue_id, issue in all_issues.items():
        if not isinstance(issue, dict):
            raise ValueError(f"issue {issue_id!r} must be a dict")
        if issue.get("id") != issue_id:
            raise ValueError(f"issue id mismatch for {issue_id!r}")
        if issue.get("status") not in _ALLOWED_ISSUE_STATUSES:
            raise ValueError(
                f"issue {issue_id!r} has invalid status {issue.get('status')!r}"
            )

        tier = issue.get("tier")
        if not isinstance(tier, int) or tier < 1 or tier > 4:
            raise ValueError(f"issue {issue_id!r} has invalid tier {tier!r}")

        reopen_count = issue.get("reopen_count")
        if not isinstance(reopen_count, int) or reopen_count < 0:
            raise ValueError(
                f"issue {issue_id!r} has invalid reopen_count {reopen_count!r}"
            )
