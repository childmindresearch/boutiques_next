"""Dynamically construct a Pydantic model for a descriptor's invocations.

``invocation_model_for(descriptor_or_subcommand)`` returns a Pydantic
``BaseModel`` subclass whose fields mirror the descriptor's inputs:
types, choices (``Literal``), optionality, and list wrapping. Sub-command
inputs recurse — a ``SubCommandInput`` becomes a nested model, a
``SubCommandUnionInput`` becomes a discriminated union over the
candidates, discriminated by an injected ``id`` literal.

Validating a raw invocation dict against this model yields free type
checking with structured Pydantic error messages.
"""

from __future__ import annotations

import operator
from functools import reduce
from typing import Annotated, Any, Literal, cast

from pydantic import BaseModel, ConfigDict, Field, create_model

from boutiques.loader import AnyDescriptor
from boutiques.models.v05.inputs import (
    FileInput,
    FlagInput,
    NumberInput,
    StringInput,
)
from boutiques.models.v05_styx.inputs import (
    SubCommandInput,
    SubCommandType,
    SubCommandUnionInput,
)


class InvocationModelError(Exception):
    """Raised when the invocation model cannot be built for a descriptor."""


def invocation_model_for(
    descriptor_or_subcommand: AnyDescriptor | SubCommandType,
) -> type[BaseModel]:
    """Return a Pydantic model that validates invocations for the given target.

    Works for top-level descriptors and recursively for ``SubCommandType``
    instances. The ``id`` discriminator field expected on sub-command
    union members is injected by ``_subcommand_model``, not here.
    """
    return _build_model(descriptor_or_subcommand, inject_id=None)


def _build_model(
    target: AnyDescriptor | SubCommandType,
    inject_id: str | None,
) -> type[BaseModel]:
    fields: dict[str, tuple[Any, Any]] = {}

    if inject_id is not None:
        # Required discriminator for SubCommandUnion members.
        fields["id"] = (Literal[inject_id], Field(...))

    inputs = target.inputs or []
    target_id = getattr(target, "id", None)
    for inp in inputs:
        py_name, py_type, default = _field_spec(inp)
        if py_name == "id" and inject_id is not None:
            raise InvocationModelError(
                f"Sub-command {target_id!r} has an input also named 'id', "
                "which collides with the discriminator field."
            )
        fields[py_name] = (py_type, default)

    name_source = getattr(target, "name", None) or target_id or "Descriptor"
    model_name = f"{_sanitize(str(name_source))}Invocation"
    config = ConfigDict(populate_by_name=True, extra="forbid")
    return cast(
        type[BaseModel],
        create_model(model_name, __config__=config, **fields),  # type: ignore[call-overload]
    )


def _field_spec(inp: Any) -> tuple[str, Any, Any]:
    """Return ``(python_field_name, python_type, pydantic_field_default)``."""
    py_name = _safe_identifier(inp.id)
    alias = inp.id

    # ``py_type`` may be a Pydantic model class, a typing alias, or a union.
    # We type it as Any so each branch can assign freely.
    py_type: Any
    if isinstance(inp, SubCommandInput):
        py_type = _build_model(inp.type, inject_id=None)
    elif isinstance(inp, SubCommandUnionInput):
        members = tuple(_build_model(sc, inject_id=sc.id) for sc in inp.type)
        union = reduce(operator.or_, members)
        py_type = Annotated[union, Field(discriminator="id")]
    else:
        base_type = _python_type_of(inp)
        is_list = bool(getattr(inp, "list_", False))
        py_type = list[base_type] if is_list else base_type  # type: ignore[valid-type]

    if inp.optional:
        py_type = py_type | None
        default = Field(default=None, alias=alias)
    else:
        default = Field(..., alias=alias)
    return py_name, py_type, default


def _python_type_of(inp: Any) -> Any:
    if isinstance(inp, FlagInput):
        return bool
    if isinstance(inp, StringInput):
        if inp.value_choices:
            return Literal[tuple(inp.value_choices)]
        return str
    if isinstance(inp, FileInput):
        return str
    if isinstance(inp, NumberInput):
        if inp.value_choices:
            return Literal[tuple(inp.value_choices)]
        return int if inp.integer else float
    raise InvocationModelError(f"Unsupported input variant: {type(inp).__name__}")


def _safe_identifier(input_id: str) -> str:
    """Map an input ID to a Pydantic-safe field name.

    Pydantic forbids field names with leading underscores (reserved for
    private attributes), and Python identifiers cannot start with a
    digit. We prefix with ``f_`` when either constraint would be violated.
    """
    if input_id and (input_id[0].isdigit() or input_id.startswith("_")):
        return f"f_{input_id}"
    return input_id


def _sanitize(name: str) -> str:
    """Sanitize a name for use in a Python class name."""
    cleaned = "".join(c if c.isalnum() else "_" for c in name)
    if cleaned and cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    return cleaned or "Descriptor"
