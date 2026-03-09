"""Compatibility alias for the legacy module path."""

from __future__ import annotations

import sys

from . import cmd as _cmd

sys.modules[__name__] = _cmd
