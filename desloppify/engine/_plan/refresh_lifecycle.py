"""Helpers for the post-flight refresh lifecycle."""

from __future__ import annotations

from typing import Iterable

from desloppify.engine._plan.constants import SYNTHETIC_PREFIXES
from desloppify.engine._plan.schema import PlanModel, ensure_plan_defaults

_POSTFLIGHT_SCAN_KEY = "postflight_scan_completed_at_scan_count"


def _refresh_state(plan: PlanModel) -> dict[str, object]:
    ensure_plan_defaults(plan)
    refresh_state = plan.get("refresh_state")
    if not isinstance(refresh_state, dict):
        refresh_state = {}
        plan["refresh_state"] = refresh_state
    return refresh_state


def _is_real_queue_issue(issue_id: str) -> bool:
    return not any(str(issue_id).startswith(prefix) for prefix in SYNTHETIC_PREFIXES)


def postflight_scan_pending(plan: PlanModel) -> bool:
    """Return True when the current empty-queue boundary still needs a scan."""
    refresh_state = plan.get("refresh_state")
    if not isinstance(refresh_state, dict):
        return True
    return not isinstance(refresh_state.get(_POSTFLIGHT_SCAN_KEY), int)


def mark_postflight_scan_completed(
    plan: PlanModel,
    *,
    scan_count: int | None,
) -> bool:
    """Record that the scan stage completed for the current refresh cycle."""
    refresh_state = _refresh_state(plan)
    try:
        normalized_scan_count = int(scan_count or 0)
    except (TypeError, ValueError):
        normalized_scan_count = 0
    if refresh_state.get(_POSTFLIGHT_SCAN_KEY) == normalized_scan_count:
        return False
    refresh_state[_POSTFLIGHT_SCAN_KEY] = normalized_scan_count
    return True


def clear_postflight_scan_completion(
    plan: PlanModel,
    *,
    issue_ids: Iterable[str] | None = None,
) -> bool:
    """Require a fresh scan after queue-changing work on real issues."""
    if issue_ids is not None and not any(
        _is_real_queue_issue(issue_id) for issue_id in issue_ids
    ):
        return False
    refresh_state = _refresh_state(plan)
    if _POSTFLIGHT_SCAN_KEY not in refresh_state:
        return False
    refresh_state.pop(_POSTFLIGHT_SCAN_KEY, None)
    return True


__all__ = [
    "clear_postflight_scan_completion",
    "mark_postflight_scan_completed",
    "postflight_scan_pending",
]
