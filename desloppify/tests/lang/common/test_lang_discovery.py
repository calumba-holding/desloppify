"""Focused tests for language discovery state handling."""

from __future__ import annotations

import importlib

import pytest

import desloppify.base.registry as core_registry_mod
import desloppify.engine._scoring.policy.core as scoring_policy_mod
from desloppify.languages import discovery as discovery_mod
from desloppify.languages import registry_state
from desloppify.languages._framework.discovery import load_all, raise_load_errors


def test_raise_load_errors_includes_module_name_and_exception_type(monkeypatch):
    monkeypatch.setattr(registry_state._STATE, "load_errors", {".dummy": ImportError("boom")})

    with pytest.raises(ImportError, match=r"\.dummy: ImportError: boom"):
        raise_load_errors()


def test_raise_load_errors_noop_when_no_errors(monkeypatch):
    monkeypatch.setattr(registry_state._STATE, "load_errors", {})
    raise_load_errors()
    assert registry_state.get_load_errors() == {}


def test_load_all_uses_plugin_file_naming_convention(monkeypatch, tmp_path):
    plugin_file = tmp_path / "plugin_rust.py"
    helper_file = tmp_path / "policy.py"
    plugin_file.write_text("# plugin placeholder\n")
    helper_file.write_text("# helper placeholder\n")

    imported: list[str] = []

    def fake_import_module(name, package=None):
        imported.append(name)
        return object()

    monkeypatch.setattr(importlib, "import_module", fake_import_module)
    monkeypatch.setattr(discovery_mod, "__file__", str(tmp_path / "discovery.py"))
    registry_state.set_load_attempted(False)
    registry_state.set_load_errors({})

    load_all()
    assert ".plugin_rust" in imported
    assert ".policy" not in imported
    assert registry_state.was_load_attempted() is True
    assert registry_state.get_load_errors() == {}
    assert len(imported) == 1


def test_load_all_force_reload_reimports_without_reset_side_effects(monkeypatch, tmp_path):
    plugin_file = tmp_path / "plugin_go.py"
    plugin_file.write_text("# plugin placeholder\n")

    imported: list[str] = []

    def fake_import_module(name, package=None):
        imported.append(name)
        return object()

    reset_calls: list[str] = []

    # Snapshot registry so we can restore after force_reload clears it.
    saved_registry = dict(registry_state.all_items())

    monkeypatch.setattr(importlib, "import_module", fake_import_module)
    monkeypatch.setattr(discovery_mod, "__file__", str(tmp_path / "discovery.py"))
    monkeypatch.setattr(
        core_registry_mod,
        "reset_registered_detectors",
        lambda: reset_calls.append("detectors"),
    )
    monkeypatch.setattr(
        scoring_policy_mod,
        "reset_registered_scoring_policies",
        lambda: reset_calls.append("scoring"),
    )
    registry_state.set_load_attempted(True)
    registry_state.set_load_errors({".stale": RuntimeError("old")})

    try:
        load_all(force_reload=True)

        # force_reload should only clear/reload language discovery state;
        # registry resets are now explicit at call sites.
        assert reset_calls == []
        assert ".plugin_go" in imported
        assert registry_state.was_load_attempted() is True
        assert registry_state.get_load_errors() == {}
    finally:
        # Restore registry contents cleared by force_reload.
        for name, cfg in saved_registry.items():
            if not registry_state.is_registered(name):
                registry_state.register(name, cfg)


def test_discovery_module_exports_expected_callables():
    assert callable(discovery_mod.load_all)
    assert callable(discovery_mod.reload_all)
    assert callable(discovery_mod.raise_load_errors)
    assert isinstance(registry_state.get_load_errors(), dict)
    assert isinstance(registry_state.was_load_attempted(), bool)
