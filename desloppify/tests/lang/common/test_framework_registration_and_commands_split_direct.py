"""Direct tests for framework command/registration/runtime helper split modules."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import desloppify.languages._framework.commands_base_registry as registry_cmd_mod
import desloppify.languages._framework.commands_base_scaffold as scaffold_mod
import desloppify.languages._framework.generic_capabilities as capabilities_mod
import desloppify.languages._framework.generic_registration as registration_mod
import desloppify.languages._framework.runtime_accessors as accessors_mod
from desloppify.languages._framework.base.types import DetectorPhase


def test_scaffold_defaults_and_registry_builder() -> None:
    registry = registry_cmd_mod.build_standard_detect_registry(
        cmd_deps=lambda _args: None,
        cmd_cycles=lambda _args: None,
        cmd_orphaned=lambda _args: None,
        cmd_dupes=lambda _args: None,
        cmd_large=lambda _args: None,
        cmd_complexity=lambda _args: None,
    )
    assert set(registry.keys()) == {
        "deps",
        "cycles",
        "orphaned",
        "dupes",
        "large",
        "complexity",
    }

    assert scaffold_mod.scaffold_find_replacements("a", "b", {}) == {}
    assert scaffold_mod.scaffold_find_self_replacements("a", "b", {}) == []
    assert scaffold_mod.scaffold_verify_hint() == "desloppify detect deps"


def test_make_cmd_deps_json_and_text_paths(monkeypatch, tmp_path) -> None:
    file_a = str((tmp_path / "a.py").resolve())
    file_b = str((tmp_path / "b.py").resolve())
    graph = {
        file_a: {
            "import_count": 1,
            "importer_count": 0,
            "imports": {file_b},
        }
    }

    cmd = registry_cmd_mod.make_cmd_deps(
        build_dep_graph_fn=lambda _path: graph,
        empty_message="No dependencies",
        import_count_label="Imports",
        top_imports_label="Top imports",
    )

    printed: list[str] = []
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: printed.append(" ".join(str(a) for a in args)))
    monkeypatch.setattr(registry_cmd_mod, "colorize", lambda text, _style: text)
    monkeypatch.setattr(registry_cmd_mod, "print_table", lambda *args, **kwargs: printed.append("TABLE"))

    cmd(SimpleNamespace(path=str(tmp_path), json=True, top=5))
    payload = json.loads(printed[-1])
    assert payload["count"] == 1
    assert payload["entries"][0]["import_count"] == 1

    printed.clear()
    cmd(SimpleNamespace(path=str(tmp_path), json=False, top=5))
    assert any("Dependency graph:" in line for line in printed)
    assert "TABLE" in printed

    cmd_empty = registry_cmd_mod.make_cmd_deps(
        build_dep_graph_fn=lambda _path: {},
        empty_message="No dependencies",
        import_count_label="Imports",
        top_imports_label="Top imports",
    )
    printed.clear()
    cmd_empty(SimpleNamespace(path=str(tmp_path), json=False, top=5))
    assert any("No dependencies" in line for line in printed)


def test_make_cmd_cycles_orphaned_and_dupes(monkeypatch, tmp_path) -> None:
    file_a = str((tmp_path / "a.py").resolve())
    file_b = str((tmp_path / "b.py").resolve())
    graph = {
        file_a: {"imports": {file_b}, "importers": set(), "import_count": 1, "importer_count": 0},
        file_b: {"imports": set(), "importers": {file_a}, "import_count": 0, "importer_count": 1},
    }

    printed: list[str] = []
    monkeypatch.setattr("builtins.print", lambda *args, **kwargs: printed.append(" ".join(str(a) for a in args)))
    monkeypatch.setattr(registry_cmd_mod, "colorize", lambda text, _style: text)
    monkeypatch.setattr(registry_cmd_mod, "print_table", lambda *args, **kwargs: printed.append("TABLE"))

    cycle_entries = [{"length": 2, "files": [file_a, file_b]}]
    monkeypatch.setattr(registry_cmd_mod, "detect_cycles", lambda _graph: (cycle_entries, 2))
    cmd_cycles = registry_cmd_mod.make_cmd_cycles(build_dep_graph_fn=lambda _path: graph)

    cmd_cycles(SimpleNamespace(path=str(tmp_path), json=True, top=5))
    payload = json.loads(printed[-1])
    assert payload["count"] == 1

    printed.clear()
    monkeypatch.setattr(registry_cmd_mod, "detect_cycles", lambda _graph: ([], 2))
    cmd_cycles(SimpleNamespace(path=str(tmp_path), json=False, top=5))
    assert any("No dependency cycles" in line for line in printed)

    orphan_entries = [{"file": file_a, "loc": 12}]
    monkeypatch.setattr(registry_cmd_mod, "detect_orphaned_files", lambda *_args, **_kwargs: (orphan_entries, 1))
    cmd_orphaned = registry_cmd_mod.make_cmd_orphaned(
        build_dep_graph_fn=lambda _path: graph,
        extensions=[".py"],
        extra_entry_patterns=["main.py"],
        extra_barrel_names={"__init__.py"},
    )

    printed.clear()
    cmd_orphaned(SimpleNamespace(path=str(tmp_path), json=True, top=5))
    payload = json.loads(printed[-1])
    assert payload["count"] == 1
    assert payload["entries"][0]["loc"] == 12

    monkeypatch.setattr(registry_cmd_mod, "detect_duplicates", lambda *_args, **_kwargs: ([
        {
            "fn_a": {"name": "a", "file": file_a, "line": 1},
            "fn_b": {"name": "b", "file": file_b, "line": 2},
            "similarity": 0.91,
            "kind": "exact",
        }
    ], 1))
    cmd_dupes = registry_cmd_mod.make_cmd_dupes(
        extract_functions_fn=lambda _path: [SimpleNamespace(name="a"), SimpleNamespace(name="b")]
    )

    printed.clear()
    cmd_dupes(SimpleNamespace(path=str(tmp_path), json=False, top=5, threshold=0.8))
    assert any("Duplicate functions:" in line for line in printed)
    assert "TABLE" in printed


def test_generic_capabilities_helpers_and_report(monkeypatch) -> None:
    monkeypatch.setattr(
        capabilities_mod,
        "find_source_files",
        lambda path, exts, excl: [f"{Path(path)}/main{exts[0]}", f"{Path(path)}/util{exts[0]}"] if excl else [],
    )

    finder = capabilities_mod.make_file_finder([".py"], exclusions=["vendor"])
    assert len(finder(Path("/tmp/project"))) == 2

    assert capabilities_mod.empty_dep_graph(Path(".")) == {}
    assert capabilities_mod.noop_extract_functions(Path(".")) == []

    rules = capabilities_mod.generic_zone_rules([".py"])
    assert rules[0].zone.value == "vendor"
    assert any(rule.zone.value == "test" for rule in rules)

    full_cfg = SimpleNamespace(integration_depth="full")
    assert capabilities_mod.capability_report(full_cfg) is None

    shallow_cfg = SimpleNamespace(
        integration_depth="shallow",
        phases=[DetectorPhase("Custom lint", lambda *_args: ([], {})), DetectorPhase("Security", lambda *_args: ([], {}))],
        fixers={"lint-fix": object()},
        build_dep_graph=lambda _path: {"a": {}},
        extract_functions=lambda _path: [],
    )
    present, missing = capabilities_mod.capability_report(shallow_cfg)
    assert "auto-fix" in present
    assert any(item.startswith("linting") for item in present)
    assert "boilerplate detection" in missing
    assert "design review" in missing


def test_generic_registration_helpers(monkeypatch) -> None:
    detector_calls: list[str] = []
    scoring_calls: list[str] = []

    monkeypatch.setattr(registration_mod, "register_detector", lambda meta: detector_calls.append(meta.name))
    monkeypatch.setattr(registration_mod, "register_scoring_policy", lambda policy: scoring_calls.append(policy.detector))
    monkeypatch.setattr(registration_mod, "make_generic_fixer", lambda tool: {"tool": tool["id"]})

    tool_specs = [
        {
            "id": "lint_errors",
            "label": "Lint errors",
            "tier": 3,
            "fix_cmd": "tool --fix",
            "cmd": "tool",
            "fmt": "rdjson",
        },
        {
            "id": "formatting",
            "label": "Formatting",
            "tier": 2,
            "fix_cmd": None,
            "cmd": "fmt",
            "fmt": "rdjson",
        },
    ]

    fixers = registration_mod._register_generic_tool_specs(tool_specs)
    assert detector_calls == ["lint_errors", "formatting"]
    assert scoring_calls == ["lint_errors", "formatting"]
    assert set(fixers.keys()) == {"lint-errors"}

    opts = registration_mod.GenericLangOptions(exclude=["vendor"], treesitter_spec=None)
    finder, extract_fn, dep_graph_fn, has_ts, ts_spec = registration_mod._resolve_generic_extractors(
        path_extensions=[".py"],
        opts=opts,
    )
    assert callable(finder)
    assert extract_fn is capabilities_mod.noop_extract_functions
    assert dep_graph_fn is capabilities_mod.empty_dep_graph
    assert has_ts is False
    assert ts_spec is None

    ts_opts = registration_mod.GenericLangOptions(
        treesitter_spec=SimpleNamespace(import_query="(import)", resolve_import=lambda *_args: None),
    )
    monkeypatch.setattr("desloppify.languages._framework.treesitter.is_available", lambda: True)
    monkeypatch.setattr(
        "desloppify.languages._framework.treesitter._extractors.make_ts_extractor",
        lambda _spec, _finder: "ts-extractor",
    )
    monkeypatch.setattr(
        "desloppify.languages._framework.treesitter._import_graph.make_ts_dep_builder",
        lambda _spec, _finder: "ts-dep-builder",
    )

    _, extract_fn, dep_graph_fn, has_ts, ts_spec = registration_mod._resolve_generic_extractors(
        path_extensions=[".py"],
        opts=ts_opts,
    )
    assert extract_fn == "ts-extractor"
    assert dep_graph_fn == "ts-dep-builder"
    assert has_ts is True
    assert ts_spec is ts_opts.treesitter_spec


def test_build_generic_phases_includes_expected_phase_sets(monkeypatch) -> None:
    monkeypatch.setattr(registration_mod, "_make_structural_phase", lambda _spec=None: DetectorPhase("Structural analysis", lambda *_args: ([], {})))
    monkeypatch.setattr(registration_mod, "_make_coupling_phase", lambda _fn: DetectorPhase("Coupling + cycles + orphaned", lambda *_args: ([], {})))

    monkeypatch.setattr(
        "desloppify.languages._framework.base.phase_builders.detector_phase_security",
        lambda: DetectorPhase("Security", lambda *_args: ([], {})),
    )
    monkeypatch.setattr(
        "desloppify.languages._framework.base.phase_builders.detector_phase_test_coverage",
        lambda: DetectorPhase("Test coverage", lambda *_args: ([], {})),
    )
    monkeypatch.setattr(
        "desloppify.languages._framework.base.phase_builders.shared_subjective_duplicates_tail",
        lambda: [DetectorPhase("Subjective review", lambda *_args: ([], {}))],
    )
    monkeypatch.setattr(
        "desloppify.languages._framework.base.phase_builders.detector_phase_signature",
        lambda: DetectorPhase("Signature analysis", lambda *_args: ([], {})),
    )
    monkeypatch.setattr(
        "desloppify.languages._framework.treesitter.phases.make_ast_smells_phase",
        lambda _spec: DetectorPhase("AST smells", lambda *_args: ([], {})),
    )
    monkeypatch.setattr(
        "desloppify.languages._framework.treesitter.phases.make_cohesion_phase",
        lambda _spec: DetectorPhase("Responsibility cohesion", lambda *_args: ([], {})),
    )
    monkeypatch.setattr(
        "desloppify.languages._framework.treesitter.phases.make_unused_imports_phase",
        lambda _spec: DetectorPhase("Unused imports", lambda *_args: ([], {})),
    )

    tool_specs = [
        {
            "id": "lint",
            "label": "Lint",
            "cmd": "lint",
            "fmt": "json",
            "tier": 3,
        }
    ]

    phases = registration_mod._build_generic_phases(
        tool_specs=tool_specs,
        ts_spec=None,
        has_treesitter=False,
        extract_fn=capabilities_mod.noop_extract_functions,
        dep_graph_fn=capabilities_mod.empty_dep_graph,
    )
    labels = [phase.label for phase in phases]
    assert "Lint" in labels
    assert "Structural analysis" in labels
    assert "Security" in labels
    assert "Coupling + cycles + orphaned" not in labels
    assert "Signature analysis" not in labels

    ts_spec = SimpleNamespace(import_query="(import)")
    phases = registration_mod._build_generic_phases(
        tool_specs=tool_specs,
        ts_spec=ts_spec,
        has_treesitter=True,
        extract_fn=lambda _path: [],
        dep_graph_fn=lambda _path: {},
    )
    labels = [phase.label for phase in phases]
    assert "AST smells" in labels
    assert "Responsibility cohesion" in labels
    assert "Unused imports" in labels
    assert "Signature analysis" in labels
    assert "Coupling + cycles + orphaned" in labels
    assert "Test coverage" in labels


class _AccessorHarness(accessors_mod.LangRunStateAccessors):
    def __init__(self):
        self.state = SimpleNamespace(
            zone_map=None,
            dep_graph=None,
            complexity_map={},
            review_cache={},
            review_max_age_days=30,
            runtime_settings={},
            runtime_options={},
            large_threshold_override=0,
            props_threshold_override=0,
            detector_coverage={},
            coverage_warnings=[],
        )
        self.config = SimpleNamespace(
            large_threshold=500,
            props_threshold=14,
            setting_specs={"flag": SimpleNamespace(default={"x": 1})},
            runtime_option_specs={"limit": SimpleNamespace(default=[1, 2, 3])},
        )


def test_runtime_accessors_cover_state_and_default_resolution() -> None:
    run = _AccessorHarness()

    run.zone_map = {"src/a.py": "production"}
    run.dep_graph = {"src/a.py": {"imports": set(), "importers": set()}}
    run.complexity_map = {"src/a.py": 4.2}
    run.review_cache = {"src/a.py": {"score": 92}}
    run.review_max_age_days = "60"
    run.runtime_settings = {"flag": {"x": 9}}
    run.runtime_options = {"limit": [9]}
    run.large_threshold_override = "800"
    run.props_threshold_override = "25"
    run.detector_coverage = {"security": {"status": "full"}}
    run.coverage_warnings = [{"detector": "security"}]

    assert run.zone_map["src/a.py"] == "production"
    assert run.dep_graph["src/a.py"]["imports"] == set()
    assert run.complexity_map["src/a.py"] == 4.2
    assert run.review_cache["src/a.py"]["score"] == 92
    assert run.review_max_age_days == 60
    assert run.runtime_settings["flag"] == {"x": 9}
    assert run.runtime_options["limit"] == [9]
    assert run.large_threshold == 800
    assert run.props_threshold == 25
    assert run.detector_coverage["security"]["status"] == "full"
    assert run.coverage_warnings[0]["detector"] == "security"

    run.large_threshold_override = 0
    run.props_threshold_override = 0
    assert run.large_threshold == 500
    assert run.props_threshold == 14

    default_setting = run.runtime_setting("flag")
    default_option = run.runtime_option("limit")
    assert default_setting == {"x": 9}
    assert default_option == [9]

    # Unknown keys should use provided defaults.
    assert run.runtime_setting("missing", default="fallback") == "fallback"
    assert run.runtime_option("missing", default=123) == 123
