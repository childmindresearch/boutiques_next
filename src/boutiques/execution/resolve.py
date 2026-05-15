"""Resolve a descriptor + invocation into a command-line string.

Substitution rules (matching the v0.5 spec, extended for SubCommand):

- For each input, locate its ``value-key`` token inside the relevant
  ``command-line`` template.
- ``Flag`` inputs: emit the ``command-line-flag`` if the value is true;
  otherwise emit nothing.
- Other inputs: format the value, prefixed by ``command-line-flag`` +
  ``command-line-flag-separator`` (default single space) when the flag
  is present.
- List inputs: items are joined with ``list-separator`` (default single
  space) before the flag prefix is applied.
- ``SubCommandInput`` / ``SubCommandUnionInput``: recursively resolve the
  nested command-line using the chosen sub-command's inputs.
- Tokens with no corresponding invocation value (optional inputs that
  were omitted) are deleted along with any leading/trailing whitespace.

Whitespace is collapsed at the end of each resolved command-line.
"""

from __future__ import annotations

import re
from typing import Any, Union

from boutiques.invocation import invocation_model_for
from boutiques.loader import AnyDescriptor
from boutiques.models.v05.inputs import FlagInput
from boutiques.models.v05_styx.inputs import (
    SubCommandInput,
    SubCommandType,
    SubCommandUnionInput,
)


def resolve(descriptor: AnyDescriptor, invocation: dict[str, Any]) -> str:
    """Validate the invocation and return the resolved command-line string."""
    model_cls = invocation_model_for(descriptor)
    parsed = model_cls.model_validate(invocation)
    values = parsed.model_dump(by_alias=True, exclude_none=True)
    return _resolve_template(descriptor.command_line, descriptor.inputs, values)


def _resolve_template(
    template: str,
    inputs: Union[list, None],
    values: dict[str, Any],
) -> str:
    command_line = template
    for inp in inputs or []:
        if not inp.value_key:
            continue
        value = values.get(inp.id)
        rendered = _render_value(inp, value)
        command_line = _substitute(command_line, inp.value_key, rendered)
    return _collapse_whitespace(command_line)


def _render_value(inp: Any, value: Any) -> str:
    if isinstance(inp, SubCommandInput):
        if value is None:
            return ""
        return _render_subcommand(inp, inp.type, value)

    if isinstance(inp, SubCommandUnionInput):
        if value is None:
            return ""
        chosen = _choose_subcommand(inp, value)
        return _render_subcommand(inp, chosen, value)

    if value is None or value is False:
        # Flag with False, or optional input not supplied.
        return ""
    if isinstance(inp, FlagInput):
        return inp.command_line_flag if value else ""

    if isinstance(value, list):
        separator = inp.list_separator if inp.list_separator is not None else " "
        body = separator.join(str(v) for v in value)
    else:
        body = str(value)

    if inp.command_line_flag:
        flag_sep = (
            inp.command_line_flag_separator
            if inp.command_line_flag_separator is not None
            else " "
        )
        return f"{inp.command_line_flag}{flag_sep}{body}"
    return body


def _render_subcommand(
    parent_input: Any,
    sub_command: SubCommandType,
    value: dict[str, Any],
) -> str:
    nested = _resolve_template(sub_command.command_line, sub_command.inputs, value)
    if parent_input.command_line_flag and nested:
        flag_sep = (
            parent_input.command_line_flag_separator
            if parent_input.command_line_flag_separator is not None
            else " "
        )
        return f"{parent_input.command_line_flag}{flag_sep}{nested}"
    return nested


def _choose_subcommand(inp: SubCommandUnionInput, value: dict[str, Any]) -> SubCommandType:
    chosen_id = value.get("id")
    for candidate in inp.type:
        if candidate.id == chosen_id:
            return candidate
    raise ValueError(
        f"Invocation for input {inp.id!r} selected sub-command id={chosen_id!r}, "
        f"but no candidate with that id exists."
    )


def _substitute(template: str, value_key: str, rendered: str) -> str:
    if rendered:
        return template.replace(value_key, rendered)
    # No value: remove the key plus any single adjacent space so we don't
    # leave a stranded gap.
    pattern = re.compile(rf"\s?{re.escape(value_key)}\s?")
    return pattern.sub(" ", template, count=1)


def _collapse_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()
