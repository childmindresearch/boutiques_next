"""Descriptor scope and input walkers shared by semantic + lint.

A "scope" is anything with ``command_line`` + ``inputs`` + (optionally)
``output_files`` — i.e. the top-level Descriptor and every nested
``SubCommandType``. The walkers yield ``(path, target)`` tuples whose
path is a JSON-pointer-style location string suitable for error
messages.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

from boutiques.loader import AnyDescriptor
from boutiques.models.v05_styx.inputs import SubCommandInput, SubCommandUnionInput


def walk_scopes(descriptor: AnyDescriptor) -> Iterator[tuple[str, Any]]:
    """Yield ``(path, scope)`` for the descriptor and each sub-command body."""
    yield "", descriptor
    for path, inp in walk_inputs(descriptor, prefix="inputs"):
        if isinstance(inp, SubCommandInput):
            yield f"{path}.type", inp.type
        elif isinstance(inp, SubCommandUnionInput):
            for i, sc in enumerate(inp.type):
                yield f"{path}.type[{i}]", sc


def walk_inputs(scope: Any, prefix: str = "inputs") -> Iterator[tuple[str, Any]]:
    """Yield ``(path, input)`` for the scope and recursively for sub-commands."""
    for i, inp in enumerate(scope.inputs or []):
        path = f"{prefix}[{i}]"
        yield path, inp
        if isinstance(inp, SubCommandInput):
            yield from walk_inputs(inp.type, prefix=f"{path}.type.inputs")
        elif isinstance(inp, SubCommandUnionInput):
            for j, sc in enumerate(inp.type):
                yield from walk_inputs(sc, prefix=f"{path}.type[{j}].inputs")
