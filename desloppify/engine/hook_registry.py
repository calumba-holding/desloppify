"""Registry for optional language hook modules consumed by detectors."""

from __future__ import annotations

import importlib
import logging
import sys
from collections import defaultdict

logger = logging.getLogger(__name__)

_hooks: dict[str, dict[str, object]] = defaultdict(dict)


def register_lang_hooks(
    lang_name: str,
    *,
    test_coverage: object | None = None,
) -> None:
    """Register optional detector hook modules for a language."""
    hooks = _hooks[lang_name]
    if test_coverage is not None:
        hooks["test_coverage"] = test_coverage


def _bootstrap_language_module(module: object) -> None:
    """Run optional language-module bootstrap hook."""
    register_fn = getattr(module, "register", None)
    if register_fn is None:
        return
    if not callable(register_fn):
        raise TypeError("Language module register entrypoint must be callable")
    register_fn()


def _get_lang_hook(
    lang_name: str | None,
    hook_name: str,
) -> object | None:
    if not lang_name:
        return None
    hook = _hooks.get(lang_name, {}).get(hook_name)
    if hook is not None:
        return hook

    module_name = f"desloppify.languages.{lang_name}"
    module = sys.modules.get(module_name)

    # Lazy-load only the requested language package.
    if module is None:
        try:
            module = importlib.import_module(module_name)
            _bootstrap_language_module(module)
        except (ImportError, ValueError, TypeError, RuntimeError, OSError) as exc:
            logger.debug(
                "Unable to import language hook package %s: %s", lang_name, exc
            )
            return None
    elif lang_name not in _hooks:
        try:
            module = importlib.reload(module)
            _bootstrap_language_module(module)
        except (ImportError, ValueError, TypeError, RuntimeError, OSError) as exc:
            logger.debug(
                "Unable to reload language hook package %s: %s", lang_name, exc
            )
            return None

    return _hooks.get(lang_name, {}).get(hook_name)


def get_lang_hook(
    lang_name: str | None,
    hook_name: str,
) -> object | None:
    """Get a previously-registered language hook module."""
    return _get_lang_hook(lang_name, hook_name)


def clear_lang_hooks_for_tests() -> None:
    """Clear registry (test helper)."""
    _hooks.clear()


__all__ = [
    "clear_lang_hooks_for_tests",
    "get_lang_hook",
    "register_lang_hooks",
]
