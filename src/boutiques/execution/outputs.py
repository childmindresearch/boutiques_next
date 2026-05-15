"""Resolve declared output paths from the invocation.

For each output:

- ``path-template``: substitute each input's ``value-key`` with the
  invocation value, stripping the extensions listed in
  ``path-template-stripped-extensions``.
- ``conditional-path-template``: a list of ``{expression: path}`` entries
  evaluated against the invocation values; the first matching expression
  wins, with the literal key ``"default"`` acting as the fallback. The
  expression dialect is the v0.5 spec's "limited python syntax"
  (``==``, ``!=``, ``<``, ``>``, ``<=``, ``>=``, ``and``, ``or``, ``not``),
  evaluated via a whitelisted AST walker — never raw ``eval`` on the
  descriptor string.

Returned paths are absolute, anchored at the launch ``cwd``.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from boutiques.loader import AnyDescriptor


@dataclass
class ResolvedOutput:
    id: str
    name: str
    path: Optional[Path]
    exists: bool


def resolve_output_paths(
    descriptor: AnyDescriptor,
    invocation: dict[str, Any],
    cwd: Path,
) -> list[ResolvedOutput]:
    """Resolve every declared output's path against the invocation values."""
    resolved: list[ResolvedOutput] = []
    for output in descriptor.output_files or []:
        path = _resolve_output(output, descriptor, invocation, cwd)
        resolved.append(
            ResolvedOutput(
                id=output.id,
                name=output.name,
                path=path,
                exists=bool(path and path.exists()),
            )
        )
    return resolved


def _resolve_output(
    output: Any,
    descriptor: AnyDescriptor,
    invocation: dict[str, Any],
    cwd: Path,
) -> Optional[Path]:
    if output.path_template is not None:
        return _substitute(output.path_template, output, descriptor, invocation, cwd)
    if output.conditional_path_template:
        chosen = _pick_conditional_template(output, descriptor, invocation)
        if chosen is None:
            return None
        return _substitute(chosen, output, descriptor, invocation, cwd)
    return None


def _substitute(
    template: str,
    output: Any,
    descriptor: AnyDescriptor,
    invocation: dict[str, Any],
    cwd: Path,
) -> Path:
    rendered = template
    stripped_exts = output.path_template_stripped_extensions or []
    for inp in descriptor.inputs:
        if not inp.value_key:
            continue
        value = invocation.get(inp.id)
        if value is None:
            continue
        value_str = _stripped(str(value), stripped_exts)
        rendered = rendered.replace(inp.value_key, value_str)
    return (cwd / rendered).resolve()


def _stripped(value: str, extensions: list[str]) -> str:
    for ext in extensions:
        if value.endswith(ext):
            return value[: -len(ext)]
    return value


# ---------------------------------------------------------------------------
# Conditional templates
# ---------------------------------------------------------------------------

def _pick_conditional_template(
    output: Any,
    descriptor: AnyDescriptor,
    invocation: dict[str, Any],
) -> Optional[str]:
    """Walk the entries; return the first matching path-template string."""
    value_map = _value_map_for_keys(descriptor, invocation)
    default: Optional[str] = None
    for entry in output.conditional_path_template or []:
        for expression, template in entry.items():
            if expression == "default":
                default = template
                continue
            if _eval_safely(expression, value_map):
                return template
    return default


def _value_map_for_keys(
    descriptor: AnyDescriptor, invocation: dict[str, Any]
) -> dict[str, Any]:
    """Map each input's value-key string to its invocation value."""
    mapping: dict[str, Any] = {}
    for inp in descriptor.inputs:
        if not inp.value_key:
            continue
        if inp.id in invocation:
            mapping[inp.value_key] = invocation[inp.id]
    return mapping


_ALLOWED_NODES = (
    ast.Expression,
    ast.BoolOp,
    ast.And,
    ast.Or,
    ast.Compare,
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.Gt,
    ast.LtE,
    ast.GtE,
    ast.Constant,
    ast.UnaryOp,
    ast.USub,
    ast.UAdd,
    ast.Not,
    ast.Load,
)


def _eval_safely(expression: str, value_map: dict[str, Any]) -> bool:
    """Evaluate a conditional expression against ``value_map``.

    Value-keys are substituted as Python literals (``repr``) so strings
    quote correctly. The resulting expression is parsed and every AST
    node is checked against an allowlist before evaluation. Any node
    outside the allowlist (function calls, attribute access, names,
    subscripts, …) raises ``ValueError``.
    """
    expr = expression
    for value_key, value in value_map.items():
        expr = expr.replace(value_key, repr(value))
    tree = ast.parse(expr, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, _ALLOWED_NODES):
            raise ValueError(
                f"Disallowed expression element {type(node).__name__!r} "
                f"in conditional-path-template: {expression!r}"
            )
    return bool(eval(compile(tree, "<conditional-path-template>", "eval")))  # noqa: S307
