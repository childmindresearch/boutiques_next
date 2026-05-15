"""Resolve a descriptor + invocation into a command-line string.

Substitution rules (matching the v0.5 spec):

- For each input, locate its ``value-key`` token inside the descriptor's
  ``command-line`` template.
- ``Flag`` inputs: emit the ``command-line-flag`` if the value is true;
  otherwise emit nothing.
- Other inputs: format the value, prefixed by ``command-line-flag`` +
  ``command-line-flag-separator`` (default single space) when the flag
  is present.
- List inputs: items are joined with ``list-separator`` (default single
  space) before the flag prefix is applied.
- Tokens with no corresponding invocation value (optional inputs that
  were omitted) are deleted along with any leading/trailing whitespace.

Whitespace is collapsed at the end.
"""

from __future__ import annotations

import re
from typing import Any

from boutiques.invocation import InvocationModelError, invocation_model_for
from boutiques.loader import AnyDescriptor
from boutiques.models.v05.inputs import FlagInput
from boutiques.models.v05_styx.inputs import SubCommandInput, SubCommandUnionInput


def resolve(descriptor: AnyDescriptor, invocation: dict[str, Any]) -> str:
    """Validate the invocation and return the resolved command-line string."""
    model_cls = invocation_model_for(descriptor)
    parsed = model_cls.model_validate(invocation)
    values = parsed.model_dump(by_alias=True, exclude_none=True)

    command_line = descriptor.command_line
    for inp in descriptor.inputs:
        if isinstance(inp, (SubCommandInput, SubCommandUnionInput)):
            raise InvocationModelError(
                f"resolve() does not yet support sub-command inputs "
                f"(input id={inp.id!r})."
            )
        if not inp.value_key:
            continue
        value = values.get(inp.id)
        rendered = _render_value(inp, value)
        command_line = _substitute(command_line, inp.value_key, rendered)

    return _collapse_whitespace(command_line)


def _render_value(inp: Any, value: Any) -> str:
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


def _substitute(template: str, value_key: str, rendered: str) -> str:
    if rendered:
        return template.replace(value_key, rendered)
    # No value: remove the key plus any single adjacent space so we don't
    # leave a stranded gap.
    pattern = re.compile(rf"\s?{re.escape(value_key)}\s?")
    return pattern.sub(" ", template, count=1)


def _collapse_whitespace(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()
