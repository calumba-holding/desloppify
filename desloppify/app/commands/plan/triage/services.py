"""Shared dependency bundle for triage command modules."""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from desloppify.app.commands.helpers.runtime import CommandRuntime, command_runtime
from desloppify.engine._state.schema import StateModel
from desloppify.engine.plan import (
    PlanModel,
    TriageInput,
    append_log_entry,
    build_triage_prompt,
    collect_triage_input,
    detect_recurring_patterns,
    extract_issue_citations,
    load_plan,
    save_plan,
)

IssueMap = dict[str, dict[str, Any]]


class AppendLogEntryFn(Protocol):
    """Typed callable contract for plan execution-log mutation."""

    def __call__(
        self,
        plan: PlanModel,
        action: str,
        *,
        issue_ids: list[str] | None = None,
        cluster_name: str | None = None,
        actor: str = "user",
        note: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> None: ...


@dataclass(frozen=True)
class TriageServices:
    """Callables shared across triage handler modules."""

    command_runtime: Callable[[argparse.Namespace], CommandRuntime]
    load_plan: Callable[[], PlanModel]
    save_plan: Callable[[PlanModel], None]
    collect_triage_input: Callable[[PlanModel, StateModel], TriageInput]
    detect_recurring_patterns: Callable[[IssueMap, IssueMap], dict[str, dict[str, list[str]]]]
    append_log_entry: AppendLogEntryFn
    extract_issue_citations: Callable[[str, set[str]], set[str]]
    build_triage_prompt: Callable[[TriageInput], str]


def default_triage_services() -> TriageServices:
    """Return the default runtime triage service bundle."""
    return TriageServices(
        command_runtime=command_runtime,
        load_plan=load_plan,
        save_plan=save_plan,
        collect_triage_input=collect_triage_input,
        detect_recurring_patterns=detect_recurring_patterns,
        append_log_entry=append_log_entry,
        extract_issue_citations=extract_issue_citations,
        build_triage_prompt=build_triage_prompt,
    )


__all__ = [
    "TriageServices",
    "default_triage_services",
]
