"""Batch execution orchestration for review command."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


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

__all__ = ["BatchRunDeps"]
