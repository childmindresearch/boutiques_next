"""Dynamically construct a Pydantic model for a descriptor's invocations.

For a given descriptor, ``invocation_model_for(descriptor)`` returns a
Pydantic ``BaseModel`` subclass whose fields mirror the descriptor's
inputs (types, constraints, optionality). Validating a raw invocation
dict against this model gives free type checking, range checks, and
choice enforcement with structured error messages.

Sub-command inputs (``SubCommandInput``, ``SubCommandUnionInput``) are
not yet handled here — they need their own discriminated-union model.
A clear error is raised when a sub-command input is encountered.
"""

from __future__ import annotations

from typing import Any, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, create_model

from boutiques.loader import AnyDescriptor
from boutiques.models.v05.inputs import (
    FileInput,
    FlagInput,
    NumberInput,
    StringInput,
)
from boutiques.models.v05_styx.inputs import SubCommandInput, SubCommandUnionInput


class InvocationModelError(Exception):
    """Raised when the invocation model cannot be built for a descriptor."""


def invocation_model_for(descriptor: AnyDescriptor) -> type[BaseModel]:
    """Return a Pydantic model that validates invocations for ``descriptor``."""
    fields: dict[str, tuple[Any, Any]] = {}
    for inp in descriptor.inputs:
        py_name, py_type, default = _field_spec(inp)
        fields[py_name] = (py_type, default)

    model_name = f"{_sanitize(descriptor.name)}Invocation"
    config = ConfigDict(populate_by_name=True, extra="forbid")
    return create_model(model_name, __config__=config, **fields)


def _field_spec(inp: Any) -> tuple[str, Any, Any]:
    """Return ``(python_field_name, python_type, pydantic_field_default)``."""
    if isinstance(inp, (SubCommandInput, SubCommandUnionInput)):
        raise InvocationModelError(
            f"Sub-command inputs are not yet supported by invocation_model_for "
            f"(input id={inp.id!r})."
        )

    base_type = _python_type_of(inp)
    is_list = bool(getattr(inp, "list_", False))
    py_type = list[base_type] if is_list else base_type  # type: ignore[valid-type]

    py_name = _safe_identifier(inp.id)
    alias = inp.id

    if inp.optional:
        py_type = Union[py_type, None]
        default = Field(default=None, alias=alias)
    else:
        default = Field(..., alias=alias)
    return py_name, py_type, default


def _python_type_of(inp: Any) -> Any:
    if isinstance(inp, FlagInput):
        return bool
    if isinstance(inp, StringInput):
        choices = inp.value_choices
        if choices:
            return Literal[tuple(choices)]  # type: ignore[valid-type]
        return str
    if isinstance(inp, FileInput):
        return str
    if isinstance(inp, NumberInput):
        choices = inp.value_choices
        if choices:
            return Literal[tuple(choices)]  # type: ignore[valid-type]
        return int if inp.integer else float
    raise InvocationModelError(f"Unsupported input variant: {type(inp).__name__}")


def _safe_identifier(input_id: str) -> str:
    """Map an input ID (which may start with a digit) to a Python identifier."""
    if input_id and input_id[0].isdigit():
        return f"_{input_id}"
    return input_id


def _sanitize(name: str) -> str:
    """Sanitize a descriptor name for use in a Python class name."""
    cleaned = "".join(c if c.isalnum() else "_" for c in name)
    if cleaned and cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    return cleaned or "Descriptor"
