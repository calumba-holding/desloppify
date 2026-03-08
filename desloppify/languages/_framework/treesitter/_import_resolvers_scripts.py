"""Import resolvers for scripting-oriented languages."""

from __future__ import annotations

import os


def resolve_ruby_import(import_text: str, source_file: str, scan_path: str) -> str | None:
    """Resolve Ruby require/require_relative to local files."""
    if import_text.startswith("./") or import_text.startswith("../"):
        base = os.path.dirname(source_file)
        candidate = os.path.normpath(os.path.join(base, import_text))
        if not candidate.endswith(".rb"):
            candidate += ".rb"
        return candidate if os.path.isfile(candidate) else None

    for base in [os.path.join(scan_path, "lib"), scan_path]:
        candidate = os.path.join(base, import_text.replace("/", os.sep))
        if not candidate.endswith(".rb"):
            candidate += ".rb"
        if os.path.isfile(candidate):
            return candidate
    return None


def resolve_php_import(import_text: str, source_file: str, scan_path: str) -> str | None:
    """Resolve PHP use statements via PSR-4-like path mapping."""
    del source_file
    parts = import_text.replace("\\", "/").split("/")
    if len(parts) < 2:
        return None

    for prefix_len in range(1, min(3, len(parts))):
        rel_path = os.path.join(*parts[prefix_len:]) + ".php"
        for src_root in ["src", "app", "lib", "."]:
            candidate = os.path.join(scan_path, src_root, rel_path)
            if os.path.isfile(candidate):
                return candidate
    return None


def resolve_lua_import(import_text: str, source_file: str, scan_path: str) -> str | None:
    """Resolve Lua require(\"foo.bar\") to local files."""
    del source_file
    if not import_text:
        return None

    rel_path = import_text.replace(".", os.sep) + ".lua"
    candidate = os.path.join(scan_path, rel_path)
    if os.path.isfile(candidate):
        return candidate

    candidate = os.path.join(scan_path, import_text.replace(".", os.sep), "init.lua")
    if os.path.isfile(candidate):
        return candidate
    return None


def resolve_js_import(import_text: str, source_file: str, scan_path: str) -> str | None:
    """Resolve JS/ESM relative imports to local files."""
    del scan_path
    if not import_text or not import_text.startswith("."):
        return None

    base = os.path.dirname(source_file)
    candidate = os.path.normpath(os.path.join(base, import_text))
    for ext in ("", ".js", ".jsx", ".mjs", ".cjs", "/index.js", "/index.jsx"):
        path = candidate + ext
        if os.path.isfile(path):
            return path
    return None


def resolve_bash_source(import_text: str, source_file: str, scan_path: str) -> str | None:
    """Resolve Bash source/. commands to local files."""
    if not import_text:
        return None

    text = import_text.strip("\"'")
    base = os.path.dirname(source_file)
    candidate = os.path.normpath(os.path.join(base, text))
    if os.path.isfile(candidate):
        return candidate
    if not candidate.endswith(".sh") and os.path.isfile(candidate + ".sh"):
        return candidate + ".sh"

    candidate = os.path.normpath(os.path.join(scan_path, text))
    return candidate if os.path.isfile(candidate) else None


_PERL_SKIP_MODULES = frozenset(
    {
        "strict",
        "warnings",
        "utf8",
        "lib",
        "constant",
        "Exporter",
        "Carp",
        "POSIX",
        "English",
        "Data::Dumper",
        "Storable",
        "Encode",
        "overload",
        "parent",
        "base",
        "vars",
        "feature",
        "mro",
    }
)
_PERL_SKIP_PREFIXES = ("File::", "List::", "Scalar::", "Getopt::", "IO::", "Test::")


def resolve_perl_import(import_text: str, source_file: str, scan_path: str) -> str | None:
    """Resolve Perl use My::Module to local .pm files."""
    del source_file
    if not import_text:
        return None
    if import_text in _PERL_SKIP_MODULES or any(
        import_text.startswith(prefix) for prefix in _PERL_SKIP_PREFIXES
    ):
        return None

    rel_path = import_text.replace("::", os.sep) + ".pm"
    for base in [os.path.join(scan_path, "lib"), scan_path]:
        candidate = os.path.join(base, rel_path)
        if os.path.isfile(candidate):
            return candidate
    return None


def resolve_r_import(import_text: str, source_file: str, scan_path: str) -> str | None:
    """Resolve R source() calls to local scripts."""
    if not import_text:
        return None

    text = import_text.strip("\"'")
    if not text.endswith((".R", ".r")):
        return None

    base = os.path.dirname(source_file)
    candidate = os.path.normpath(os.path.join(base, text))
    if os.path.isfile(candidate):
        return candidate

    for src_root in [".", "R"]:
        candidate = os.path.join(scan_path, src_root, text)
        if os.path.isfile(candidate):
            return candidate
    return None
