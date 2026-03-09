from __future__ import annotations

from desloppify.engine._plan.refresh_lifecycle import (
    clear_postflight_scan_completion,
    mark_postflight_scan_completed,
    postflight_scan_pending,
)
from desloppify.engine._plan.schema import empty_plan


def test_postflight_scan_pending_until_completed() -> None:
    plan = empty_plan()

    assert postflight_scan_pending(plan) is True

    changed = mark_postflight_scan_completed(plan, scan_count=7)

    assert changed is True
    assert postflight_scan_pending(plan) is False
    assert plan["refresh_state"]["postflight_scan_completed_at_scan_count"] == 7


def test_clearing_completion_ignores_synthetic_ids() -> None:
    plan = empty_plan()
    mark_postflight_scan_completed(plan, scan_count=3)

    changed = clear_postflight_scan_completion(
        plan,
        issue_ids=["workflow::run-scan", "triage::observe", "subjective::naming_quality"],
    )

    assert changed is False
    assert postflight_scan_pending(plan) is False


def test_clearing_completion_for_real_issue_requires_new_scan() -> None:
    plan = empty_plan()
    mark_postflight_scan_completed(plan, scan_count=5)

    changed = clear_postflight_scan_completion(
        plan,
        issue_ids=["unused::src/app.ts::thing"],
    )

    assert changed is True
    assert postflight_scan_pending(plan) is True
