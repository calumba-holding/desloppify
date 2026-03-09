"""Canonical detector registry — single source of truth.

All detector metadata lives here. Other modules derive their views
(display order, CLI names, narrative tools, scoring validation) from this registry
instead of maintaining their own lists.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from desloppify.base.registry_catalog_entries import DETECTORS as _CATALOG_DETECTORS
from desloppify.base.registry_catalog_models import DISPLAY_ORDER, DetectorMeta

_BASE_DETECTORS: dict[str, DetectorMeta] = dict(_CATALOG_DETECTORS)
_BASE_DISPLAY_ORDER: list[str] = list(DISPLAY_ORDER)
_BASE_JUDGMENT_DETECTORS: frozenset[str] = frozenset(
    name for name, meta in _BASE_DETECTORS.items() if meta.needs_judgment
)

DETECTORS: dict[str, DetectorMeta] = dict(_CATALOG_DETECTORS)
_DISPLAY_ORDER: list[str] = list(DISPLAY_ORDER)
_on_register_callbacks: list[Callable[[], None]] = []

JUDGMENT_DETECTORS: frozenset[str] = frozenset(
    name for name, meta in DETECTORS.items() if meta.needs_judgment
)


def on_detector_registered(callback: Callable[[], None]) -> None:
    """Register a callback invoked after register_detector(). No-arg."""
    _on_register_callbacks.append(callback)


def register_detector(meta: DetectorMeta) -> None:
    """Register a detector at runtime (used by generic plugins)."""
    global JUDGMENT_DETECTORS
    DETECTORS[meta.name] = meta
    if meta.name not in _DISPLAY_ORDER:
        _DISPLAY_ORDER.append(meta.name)
    JUDGMENT_DETECTORS = frozenset(
        name for name, current_meta in DETECTORS.items()
        if current_meta.needs_judgment
    )
    for callback in tuple(_on_register_callbacks):
        callback()


def reset_registered_detectors() -> None:
    """Reset runtime-added detector registrations to built-in defaults."""
    global JUDGMENT_DETECTORS
    DETECTORS.clear()
    DETECTORS.update(_BASE_DETECTORS)
    _DISPLAY_ORDER.clear()
    _DISPLAY_ORDER.extend(_BASE_DISPLAY_ORDER)
    JUDGMENT_DETECTORS = _BASE_JUDGMENT_DETECTORS
    for callback in tuple(_on_register_callbacks):
        callback()


def detector_names() -> list[str]:
    """All registered detector names, sorted."""
    return sorted(DETECTORS.keys())


def display_order() -> list[str]:
    """Canonical display order for terminal output."""
    return list(_DISPLAY_ORDER)


_ACTION_PRIORITY = {"auto_fix": 0, "reorganize": 1, "refactor": 2, "manual_fix": 3}
_ACTION_LABELS = {
    "auto_fix": "autofix",
    "reorganize": "move",
    "refactor": "refactor",
    "manual_fix": "manual",
}


def dimension_action_type(dim_name: str) -> str:
    """Return a compact action type label for a dimension based on its detectors."""
    best = "manual"
    best_priority = 99
    for detector_meta in DETECTORS.values():
        if detector_meta.dimension == dim_name:
            priority = _ACTION_PRIORITY.get(detector_meta.action_type, 99)
            if priority < best_priority:
                best_priority = priority
                best = detector_meta.action_type
    return _ACTION_LABELS.get(best, "manual")


def detector_tools() -> dict[str, dict[str, Any]]:
    """Build detector tool metadata keyed by detector name."""
    result = {}
    for detector_name, detector_meta in DETECTORS.items():
        entry: dict[str, Any] = {
            "fixers": list(detector_meta.fixers),
            "action_type": detector_meta.action_type,
        }
        if detector_meta.tool:
            entry["tool"] = detector_meta.tool
        if detector_meta.guidance:
            entry["guidance"] = detector_meta.guidance
        result[detector_name] = entry
    return result


__all__ = [
    "DETECTORS",
    "DISPLAY_ORDER",
    "DetectorMeta",
    "JUDGMENT_DETECTORS",
    "_DISPLAY_ORDER",
    "_on_register_callbacks",
    "detector_names",
    "detector_tools",
    "dimension_action_type",
    "display_order",
    "on_detector_registered",
    "register_detector",
    "reset_registered_detectors",
]
