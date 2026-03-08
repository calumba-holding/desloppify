"""Per-language tree-sitter import resolution helpers.

Compatibility facade that re-exports resolver functions from focused modules.
"""

from __future__ import annotations

from ._import_resolvers_backend import (
    resolve_csharp_import,
    resolve_cxx_include,
    resolve_dart_import,
    resolve_go_import,
    resolve_java_import,
    resolve_kotlin_import,
    resolve_rust_import,
    resolve_scala_import,
    resolve_swift_import,
)
from ._import_resolvers_functional import (
    resolve_elixir_import,
    resolve_erlang_include,
    resolve_fsharp_import,
    resolve_haskell_import,
    resolve_ocaml_import,
    resolve_zig_import,
)
from ._import_resolvers_scripts import (
    resolve_bash_source,
    resolve_js_import,
    resolve_lua_import,
    resolve_perl_import,
    resolve_php_import,
    resolve_r_import,
    resolve_ruby_import,
)

__all__ = [
    "resolve_bash_source",
    "resolve_csharp_import",
    "resolve_cxx_include",
    "resolve_dart_import",
    "resolve_elixir_import",
    "resolve_erlang_include",
    "resolve_fsharp_import",
    "resolve_go_import",
    "resolve_haskell_import",
    "resolve_java_import",
    "resolve_js_import",
    "resolve_kotlin_import",
    "resolve_lua_import",
    "resolve_ocaml_import",
    "resolve_perl_import",
    "resolve_php_import",
    "resolve_r_import",
    "resolve_ruby_import",
    "resolve_rust_import",
    "resolve_scala_import",
    "resolve_swift_import",
    "resolve_zig_import",
]
