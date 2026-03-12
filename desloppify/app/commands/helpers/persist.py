"""Legacy wrapper for command persistence helpers."""

from desloppify.app.commands.helpers.state_persistence import (
    save_config_or_exit,
    save_state_or_exit,
)

__all__ = ["save_config_or_exit", "save_state_or_exit"]
