"""Shared constants for plan internals."""

from __future__ import annotations

from dataclasses import dataclass, field

AUTO_PREFIX = "auto/"

SUBJECTIVE_PREFIX = "subjective::"
TRIAGE_ID = "triage::pending"  # deprecated, kept for migration

TRIAGE_PREFIX = "triage::"
TRIAGE_STAGE_IDS = (
    "triage::observe",
    "triage::reflect",
    "triage::organize",
    "triage::enrich",
    "triage::sense-check",
    "triage::commit",
)
TRIAGE_IDS = set(TRIAGE_STAGE_IDS)
WORKFLOW_CREATE_PLAN_ID = "workflow::create-plan"
WORKFLOW_SCORE_CHECKPOINT_ID = "workflow::score-checkpoint"
WORKFLOW_IMPORT_SCORES_ID = "workflow::import-scores"
WORKFLOW_COMMUNICATE_SCORE_ID = "workflow::communicate-score"
WORKFLOW_PREFIX = "workflow::"
SYNTHETIC_PREFIXES = ("triage::", "workflow::", "subjective::")


@dataclass
class QueueSyncResult:
    """Unified result for all queue sync operations."""

    injected: list[str] = field(default_factory=list)
    pruned: list[str] = field(default_factory=list)
    deferred: bool = False

    @property
    def changes(self) -> int:
        return len(self.injected) + len(self.pruned)


__all__ = [
    "AUTO_PREFIX",
    "QueueSyncResult",
    "SUBJECTIVE_PREFIX",
    "SYNTHETIC_PREFIXES",
    "TRIAGE_IDS",
    "TRIAGE_PREFIX",
    "TRIAGE_STAGE_IDS",
    "WORKFLOW_COMMUNICATE_SCORE_ID",
    "WORKFLOW_CREATE_PLAN_ID",
    "WORKFLOW_IMPORT_SCORES_ID",
    "WORKFLOW_PREFIX",
    "WORKFLOW_SCORE_CHECKPOINT_ID",
]
