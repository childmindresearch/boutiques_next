"""Cross-field semantic validation.

Pydantic enforces *shape* — types, required fields, list bounds. This
module enforces the *relationships* between fields that the original
v0.5 JSON Schema expressed via its ``dependencies`` block, plus a few
descriptor-wide invariants (unique IDs, value-keys must appear in the
command-line they belong to, group members must reference real inputs).

Each rule returns ``ValidationError`` instances with a JSON-pointer-like
``location``. The aggregate is returned by :func:`check`.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator
from typing import Any

from boutiques._errors import ValidationError
from boutiques.loader import AnyDescriptor
from boutiques.models.v05_styx.inputs import (
    SubCommandInput,
    SubCommandUnionInput,
)


def check(descriptor: AnyDescriptor) -> list[ValidationError]:
    """Run all semantic checks; return every error found."""
    errors: list[ValidationError] = []

    # Per-scope (top-level descriptor + each sub-command body)
    for scope_path, scope in _walk_scopes(descriptor):
        errors.extend(_check_unique_input_ids(scope, scope_path))
        errors.extend(_check_unique_value_keys(scope, scope_path))
        errors.extend(_check_value_keys_in_command_line(scope, scope_path))

    # Per-input (recursive into sub-commands)
    for path, inp in _walk_inputs(descriptor, prefix="inputs"):
        errors.extend(_check_input_dependencies(inp, path))

    # Descriptor-wide
    errors.extend(_check_groups(descriptor))
    errors.extend(_check_outputs(descriptor))
    errors.extend(_check_subcommand_union_ids(descriptor))

    return errors


# ---------------------------------------------------------------------------
# Walking helpers
# ---------------------------------------------------------------------------


def _walk_scopes(descriptor: AnyDescriptor) -> Iterator[tuple[str, Any]]:
    """Yield ``(path, scope)`` for the descriptor and each sub-command body.

    A "scope" is anything with a ``command_line`` and ``inputs`` — i.e.
    the top-level descriptor and every ``SubCommandType``.
    """
    yield "", descriptor
    for path, inp in _walk_inputs(descriptor, prefix="inputs"):
        if isinstance(inp, SubCommandInput):
            yield f"{path}.type", inp.type
        elif isinstance(inp, SubCommandUnionInput):
            for i, sc in enumerate(inp.type):
                yield f"{path}.type[{i}]", sc


def _walk_inputs(scope: Any, prefix: str) -> Iterator[tuple[str, Any]]:
    """Yield ``(path, input)`` for the scope and recursively for sub-commands."""
    for i, inp in enumerate(scope.inputs or []):
        path = f"{prefix}[{i}]"
        yield path, inp
        if isinstance(inp, SubCommandInput):
            yield from _walk_inputs(inp.type, prefix=f"{path}.type.inputs")
        elif isinstance(inp, SubCommandUnionInput):
            for j, sc in enumerate(inp.type):
                yield from _walk_inputs(sc, prefix=f"{path}.type[{j}].inputs")


# ---------------------------------------------------------------------------
# Per-scope checks
# ---------------------------------------------------------------------------


def _check_unique_input_ids(scope: Any, scope_path: str) -> list[ValidationError]:
    counts = Counter(inp.id for inp in (scope.inputs or []))
    location_prefix = f"{scope_path}." if scope_path else ""
    return [
        ValidationError(
            location=f"{location_prefix}inputs",
            message=f"Duplicate input id {id_!r} ({n} occurrences).",
        )
        for id_, n in counts.items()
        if n > 1
    ]


def _check_unique_value_keys(scope: Any, scope_path: str) -> list[ValidationError]:
    keys = [inp.value_key for inp in (scope.inputs or []) if getattr(inp, "value_key", None)]
    counts = Counter(keys)
    location_prefix = f"{scope_path}." if scope_path else ""
    return [
        ValidationError(
            location=f"{location_prefix}inputs",
            message=f"Duplicate value-key {key!r} ({n} occurrences).",
        )
        for key, n in counts.items()
        if n > 1
    ]


def _check_value_keys_in_command_line(scope: Any, scope_path: str) -> list[ValidationError]:
    """Every input's value-key must appear in the scope's command-line."""
    command_line = scope.command_line
    errors: list[ValidationError] = []
    for i, inp in enumerate(scope.inputs or []):
        vk = getattr(inp, "value_key", None)
        if not vk:
            continue
        if vk not in command_line:
            location_prefix = f"{scope_path}." if scope_path else ""
            errors.append(
                ValidationError(
                    location=f"{location_prefix}inputs[{i}].value-key",
                    message=(
                        f"value-key {vk!r} does not appear in the command-line {command_line!r}."
                    ),
                )
            )
    return errors


# ---------------------------------------------------------------------------
# Per-input dependency checks
# ---------------------------------------------------------------------------


def _check_input_dependencies(inp: Any, path: str) -> list[ValidationError]:
    """The dependency block from the v0.5 JSON Schema, plus min<=max bounds."""
    errors: list[ValidationError] = []

    def require(child_attr: str, parent_attr: str, parent_label: str) -> None:
        child = getattr(inp, child_attr, None)
        parent = getattr(inp, parent_attr, None)
        if child is not None and child is not False and parent in (None, False):
            errors.append(
                ValidationError(
                    location=f"{path}.{_alias(child_attr)}",
                    message=f"{_alias(child_attr)!r} requires {parent_label!r} to be set.",
                )
            )

    require("command_line_flag_separator", "command_line_flag", "command-line-flag")
    require("min_list_entries", "list_", "list")
    require("max_list_entries", "list_", "list")
    require("list_separator", "list_", "list")
    require("exclusive_minimum", "minimum", "minimum")
    require("exclusive_maximum", "maximum", "maximum")
    require("value_disables", "value_choices", "value-choices")
    require("value_enables", "value_choices", "value-choices")
    require("value_requires", "value_choices", "value-choices")

    # min/max bounds
    minimum = getattr(inp, "minimum", None)
    maximum = getattr(inp, "maximum", None)
    if minimum is not None and maximum is not None and minimum > maximum:
        errors.append(
            ValidationError(
                location=f"{path}.minimum",
                message=f"minimum ({minimum}) must be <= maximum ({maximum}).",
            )
        )

    min_list = getattr(inp, "min_list_entries", None)
    max_list = getattr(inp, "max_list_entries", None)
    if min_list is not None and max_list is not None and min_list > max_list:
        errors.append(
            ValidationError(
                location=f"{path}.min-list-entries",
                message=(
                    f"min-list-entries ({min_list}) must be <= max-list-entries ({max_list})."
                ),
            )
        )

    return errors


def _alias(python_attr: str) -> str:
    """Map a Python attribute name to its descriptor alias."""
    # Strip trailing underscore (list_ -> list), then dash-ify.
    name = python_attr.rstrip("_")
    return name.replace("_", "-")


# ---------------------------------------------------------------------------
# Descriptor-wide checks
# ---------------------------------------------------------------------------


def _check_groups(descriptor: AnyDescriptor) -> list[ValidationError]:
    """Every group member must reference an existing top-level input id."""
    if not descriptor.groups:
        return []
    input_ids = {inp.id for inp in descriptor.inputs}
    errors: list[ValidationError] = []
    for gi, group in enumerate(descriptor.groups):
        for mi, member in enumerate(group.members):
            if member not in input_ids:
                errors.append(
                    ValidationError(
                        location=f"groups[{gi}].members[{mi}]",
                        message=(f"Group {group.id!r} references unknown input id {member!r}."),
                    )
                )
    return errors


def _check_outputs(descriptor: AnyDescriptor) -> list[ValidationError]:
    """Output ids must be unique."""
    if not descriptor.output_files:
        return []
    counts = Counter(o.id for o in descriptor.output_files)
    return [
        ValidationError(
            location="output-files",
            message=f"Duplicate output id {id_!r} ({n} occurrences).",
        )
        for id_, n in counts.items()
        if n > 1
    ]


def _check_subcommand_union_ids(descriptor: AnyDescriptor) -> list[ValidationError]:
    """Within a SubCommandUnion, candidate ids must be unique (the discriminator)."""
    errors: list[ValidationError] = []
    for path, inp in _walk_inputs(descriptor, prefix="inputs"):
        if not isinstance(inp, SubCommandUnionInput):
            continue
        counts = Counter(sc.id for sc in inp.type)
        for id_, n in counts.items():
            if n > 1:
                errors.append(
                    ValidationError(
                        location=f"{path}.type",
                        message=(
                            f"Sub-command union candidates must have unique ids; "
                            f"id {id_!r} appears {n} times."
                        ),
                    )
                )
    return errors


