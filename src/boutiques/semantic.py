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

import re
from collections import Counter
from typing import Any

from boutiques._errors import ValidationError
from boutiques._walk import walk_inputs, walk_scopes
from boutiques.loader import AnyDescriptor
from boutiques.models.v05_styx.inputs import SubCommandUnionInput

_VALUE_KEY_RE = re.compile(r"\[([A-Z0-9_]+)\]")


def check(descriptor: AnyDescriptor) -> list[ValidationError]:
    """Run all semantic checks; return every error found."""
    errors: list[ValidationError] = []

    # Per-scope (top-level descriptor + each sub-command body)
    for scope_path, scope in walk_scopes(descriptor):
        errors.extend(_check_unique_input_ids(scope, scope_path))
        errors.extend(_check_unique_value_keys(scope, scope_path))
        errors.extend(_check_value_keys_in_command_line(scope, scope_path))
        errors.extend(_check_unique_output_ids(scope, scope_path))
        errors.extend(_check_unique_output_path_templates(scope, scope_path))
        errors.extend(_check_orphan_command_line_tokens(scope, scope_path))

    # Per-input (recursive into sub-commands)
    for path, inp in walk_inputs(descriptor):
        errors.extend(_check_input_dependencies(inp, path))

    # Descriptor-wide
    errors.extend(_check_groups(descriptor))
    errors.extend(_check_subcommand_union_ids(descriptor))

    return errors


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


def _check_unique_output_ids(scope: Any, scope_path: str) -> list[ValidationError]:
    """Output ids must be unique within a scope."""
    output_files = getattr(scope, "output_files", None)
    if not output_files:
        return []
    counts = Counter(o.id for o in output_files)
    prefix = f"{scope_path}." if scope_path else ""
    return [
        ValidationError(
            location=f"{prefix}output-files",
            message=f"Duplicate output id {id_!r} ({n} occurrences).",
        )
        for id_, n in counts.items()
        if n > 1
    ]


def _check_unique_output_path_templates(scope: Any, scope_path: str) -> list[ValidationError]:
    """No two outputs in a scope may declare the same literal ``path-template``."""
    output_files = getattr(scope, "output_files", None)
    if not output_files:
        return []
    counts: Counter[str] = Counter()
    for output in output_files:
        if output.path_template:
            counts[output.path_template] += 1
    prefix = f"{scope_path}." if scope_path else ""
    return [
        ValidationError(
            location=f"{prefix}output-files",
            message=f"Duplicate path-template {pt!r} ({n} occurrences).",
        )
        for pt, n in counts.items()
        if n > 1
    ]


def _check_orphan_command_line_tokens(scope: Any, scope_path: str) -> list[ValidationError]:
    """``[UPPER_CASE]`` tokens in a scope's command-line must have a matching value-key.

    Orphan tokens stay literally in the resolved command, which is almost
    always a descriptor bug. We only match the conventional ``[UPPER_CASE]``
    form so descriptors with non-standard value-keys (lowercase, mixed, etc.)
    aren't false-flagged.
    """
    command_line = getattr(scope, "command_line", None) or ""
    tokens_in_cli = set(_VALUE_KEY_RE.findall(command_line))
    if not tokens_in_cli:
        return []
    declared = {
        getattr(inp, "value_key", None) for inp in (scope.inputs or [])
    }
    declared.discard(None)
    orphans = sorted(t for t in tokens_in_cli if f"[{t}]" not in declared)
    prefix = f"{scope_path}." if scope_path else ""
    return [
        ValidationError(
            location=f"{prefix}command-line",
            message=f"Command-line contains token [{t}] with no matching input value-key.",
        )
        for t in orphans
    ]


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


def _check_subcommand_union_ids(descriptor: AnyDescriptor) -> list[ValidationError]:
    """Within a SubCommandUnion, candidate ids must be unique (the discriminator)."""
    errors: list[ValidationError] = []
    for path, inp in walk_inputs(descriptor):
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


