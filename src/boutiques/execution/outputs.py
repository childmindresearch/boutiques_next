"""Resolve declared output paths from the invocation.

For each output:

- ``path-template``: substitute each input's ``value-key`` with the
  invocation value, stripping the extensions listed in
  ``path-template-stripped-extensions``.
- ``conditional-path-template``: not yet supported. The output is
  reported with ``path=None`` so the caller knows it was deferred.

Returned paths are absolute, anchored at the launch ``cwd``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from boutiques.loader import AnyDescriptor


@dataclass
class ResolvedOutput:
    id: str
    name: str
    path: Optional[Path]  # None when the template is conditional / unresolvable
    exists: bool


def resolve_output_paths(
    descriptor: AnyDescriptor,
    invocation: dict[str, Any],
    cwd: Path,
) -> list[ResolvedOutput]:
    """Resolve every declared output's path against the invocation values."""
    resolved: list[ResolvedOutput] = []
    for output in descriptor.output_files or []:
        path = _resolve_path_template(output, descriptor, invocation, cwd)
        resolved.append(
            ResolvedOutput(
                id=output.id,
                name=output.name,
                path=path,
                exists=bool(path and path.exists()),
            )
        )
    return resolved


def _resolve_path_template(
    output: Any,
    descriptor: AnyDescriptor,
    invocation: dict[str, Any],
    cwd: Path,
) -> Optional[Path]:
    if output.path_template is None:
        # conditional-path-template not yet supported.
        return None
    rendered = output.path_template
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
