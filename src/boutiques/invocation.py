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


def invocation_schema(descriptor: AnyDescriptor) -> dict[str, Any]:
    """Return a JSON Schema describing valid invocations for ``descriptor``.

    Produced by introspecting the dynamic Pydantic model from
    :func:`invocation_model_for`. The schema captures required vs. optional
    inputs, value-choices as ``enum``, numeric ranges, list bounds, and
    sub-command unions as discriminated ``oneOf`` branches — i.e.
    everything the runtime invocation enforcement checks structurally.
    """
    return invocation_model_for(descriptor).model_json_schema()


#: JSON key that tags each SubCommandUnion branch. Matches Styx's convention
#: (``@type``) so invocations are interchangeable between this toolkit and
#: Styx-generated language bindings.
DISCRIMINATOR_KEY = "@type"

#: Pydantic-safe Python field name backing :data:`DISCRIMINATOR_KEY`. Pydantic
#: forbids leading-underscore field names and disallows ``@`` in identifiers,
#: so we use ``type_`` and route the JSON key through an alias.
_DISCRIMINATOR_PY_NAME = "type_"


def _build_model(
    target: AnyDescriptor | SubCommandType,
    inject_id: str | None,
) -> type[BaseModel]:
    fields: dict[str, tuple[Any, Any]] = {}

    if inject_id is not None:
        # Required discriminator for SubCommandUnion members.
        fields[_DISCRIMINATOR_PY_NAME] = (
            Literal[inject_id],
            Field(..., alias=DISCRIMINATOR_KEY),
        )

    inputs = target.inputs or []
    target_id = getattr(target, "id", None)
    for inp in inputs:
        py_name, py_type, default = _field_spec(inp)
        if inject_id is not None and (
            py_name == _DISCRIMINATOR_PY_NAME or inp.id == DISCRIMINATOR_KEY
        ):
            raise InvocationModelError(
                f"Sub-command {target_id!r} has an input that collides with "
                f"the {DISCRIMINATOR_KEY!r} discriminator field."
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
    extra: dict[str, Any] = {}
    if isinstance(inp, SubCommandInput):
        py_type = _build_model(inp.type, inject_id=None)
    elif isinstance(inp, SubCommandUnionInput):
        members = tuple(_build_model(sc, inject_id=sc.id) for sc in inp.type)
        union = reduce(operator.or_, members)
        py_type = Annotated[union, Field(discriminator=_DISCRIMINATOR_PY_NAME)]
    else:
        base_type = _python_type_of(inp)
        is_list = bool(getattr(inp, "list_", False))
        py_type = list[base_type] if is_list else base_type  # type: ignore[valid-type]
        extra.update(_constraint_kwargs(inp, is_list))

    if inp.optional:
        py_type = py_type | None
        default = Field(default=None, alias=alias, **extra)
    else:
        default = Field(..., alias=alias, **extra)
    return py_name, py_type, default


def _constraint_kwargs(inp: Any, is_list: bool) -> dict[str, Any]:
    """Pydantic ``Field`` kwargs derived from the input's range/list-bound attrs.

    - ``Number`` inputs: ``ge``/``gt``/``le``/``lt`` from
      ``minimum``/``maximum`` (honoring ``exclusive-minimum``/``exclusive-maximum``).
      Skipped when ``value-choices`` is set, since ``Literal`` already
      enforces the closed set.
    - List inputs: ``min_length`` / ``max_length`` from
      ``min-list-entries`` / ``max-list-entries``.
    """
    kwargs: dict[str, Any] = {}

    if isinstance(inp, NumberInput) and not inp.value_choices:
        if inp.minimum is not None:
            key = "gt" if inp.exclusive_minimum else "ge"
            kwargs[key] = inp.minimum
        if inp.maximum is not None:
            key = "lt" if inp.exclusive_maximum else "le"
            kwargs[key] = inp.maximum

    if is_list:
        if inp.min_list_entries is not None:
            kwargs["min_length"] = int(inp.min_list_entries)
        if inp.max_list_entries is not None:
            kwargs["max_length"] = int(inp.max_list_entries)

    return kwargs


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


# Names that exist on ``pydantic.BaseModel`` (or its inherited bases like
# ``abc.ABCMeta``). Using any of these as a field name triggers a Pydantic
# UserWarning about shadowing. Real-world niwrap descriptors hit ``register``,
# ``copy``, ``json``; the rest are common deprecated v1 / object-level
# attributes that would conflict if a descriptor used them as an input id.
_SHADOWS_BASEMODEL = frozenset(
    {
        "construct",
        "copy",
        "dict",
        "from_orm",
        "json",
        "model_computed_fields",
        "model_config",
        "model_extra",
        "model_fields",
        "model_fields_set",
        "parse_file",
        "parse_obj",
        "parse_raw",
        "register",
        "schema",
        "schema_json",
        "update_forward_refs",
        "validate",
    }
)


def _safe_identifier(input_id: str) -> str:
    """Map an input ID to a Pydantic-safe field name.

    Three constraints handled:

    - Python identifiers cannot start with a digit.
    - Pydantic forbids field names that start with an underscore (those
      are reserved for private attributes).
    - A field name that matches an attribute on ``pydantic.BaseModel``
      triggers a UserWarning about shadowing. ``register``, ``copy``,
      and ``json`` all occur in real-world descriptors.

    For the first two we prefix ``f_``; for the shadow case we append
    a trailing underscore. The descriptor's alias (the original input
    id) is always preserved on the Pydantic ``Field``, so JSON
    invocations are untouched.
    """
    if input_id and (input_id[0].isdigit() or input_id.startswith("_")):
        return f"f_{input_id}"
    if input_id in _SHADOWS_BASEMODEL:
        return f"{input_id}_"
    return input_id


def _sanitize(name: str) -> str:
    """Sanitize a name for use in a Python class name."""
    cleaned = "".join(c if c.isalnum() else "_" for c in name)
    if cleaned and cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    return cleaned or "Descriptor"
