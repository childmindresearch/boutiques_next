"""Compute container bind-mount paths from a descriptor + invocation.

For every File-typed input present in the invocation (recursive into
sub-commands), the absolute parent directory of the file path is added
to the mount set. Paths that are descendants of another planned mount
are dropped, since the broader mount already covers them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from boutiques.loader import AnyDescriptor
from boutiques.models.v05.inputs import FileInput
from boutiques.models.v05_styx.inputs import (
    SubCommandInput,
    SubCommandType,
    SubCommandUnionInput,
)


def collect_file_mounts(
    descriptor: AnyDescriptor,
    invocation: dict[str, Any],
) -> list[Path]:
    """Return absolute parent dirs of every File-typed value in the invocation."""
    raw: set[Path] = set()
    for path_str in _iter_file_paths(descriptor.inputs, invocation):
        if not path_str:
            continue
        raw.add(Path(path_str).expanduser().resolve().parent)
    return _dedupe_descendants(raw)


def _iter_file_paths(inputs, values: dict[str, Any]) -> Iterator[str]:
    for inp in inputs or []:
        value = values.get(inp.id)
        if value is None:
            continue
        if isinstance(inp, FileInput):
            if isinstance(value, list):
                yield from (str(v) for v in value if v)
            elif value:
                yield str(value)
        elif isinstance(inp, SubCommandInput):
            yield from _iter_file_paths(inp.type.inputs, value or {})
        elif isinstance(inp, SubCommandUnionInput):
            chosen = _chosen_subcommand(inp, value)
            if chosen is not None:
                yield from _iter_file_paths(chosen.inputs, value)


def _chosen_subcommand(
    inp: SubCommandUnionInput, value: Any
) -> SubCommandType | None:
    if not isinstance(value, dict):
        return None
    chosen_id = value.get("id")
    for candidate in inp.type:
        if candidate.id == chosen_id:
            return candidate
    return None


def _dedupe_descendants(paths: set[Path]) -> list[Path]:
    """Drop paths that are inside another path already in the set."""
    # Process shortest paths first so they get picked over their children.
    sorted_paths = sorted(paths, key=lambda p: len(p.parts))
    kept: list[Path] = []
    for p in sorted_paths:
        if any(_is_within(p, anchor) for anchor in kept):
            continue
        kept.append(p)
    return kept


def _is_within(child: Path, ancestor: Path) -> bool:
    try:
        child.relative_to(ancestor)
        return True
    except ValueError:
        return False
