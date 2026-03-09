"""Batch execution orchestration for review command."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .execution_phases import (
    execute_batch_run,
    merge_and_import_batch_run,
    prepare_batch_run,
)


@dataclass(frozen=True)
class BatchRunDeps:
    """Injected dependencies for batch-run phases."""

    run_stamp_fn: Any
    load_or_prepare_packet_fn: Any
    selected_batch_indexes_fn: Any
    prepare_run_artifacts_fn: Any
    run_codex_batch_fn: Any
    execute_batches_fn: Any
    collect_batch_results_fn: Any
    print_failures_fn: Any
    print_failures_and_raise_fn: Any
    merge_batch_results_fn: Any
    build_import_provenance_fn: Any
    do_import_fn: Any
    run_followup_scan_fn: Any
    safe_write_text_fn: Any
    colorize_fn: Any


def do_run_batches(
    args,
    state,
    lang,
    state_file,
    *,
    config: dict[str, Any] | None,
    deps: BatchRunDeps,
    project_root: Path,
    subagent_runs_dir: Path,
) -> None:
    """Run holistic investigation batches with a local subagent runner."""
    prepared = prepare_batch_run(
        args=args,
        state=state,
        lang=lang,
        config=config or {},
        deps=deps,
        project_root=project_root,
        subagent_runs_dir=subagent_runs_dir,
    )
    if prepared is None:
        return

    executed = execute_batch_run(prepared=prepared, deps=deps)
    merge_and_import_batch_run(
        prepared=prepared,
        executed=executed,
        state_file=state_file,
        deps=deps,
    )


__all__ = ["BatchRunDeps", "do_run_batches"]
