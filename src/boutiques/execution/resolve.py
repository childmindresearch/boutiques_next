"""Resolve a descriptor + invocation into an argv token list.

The template is tokenized once via :func:`shlex.split`. Each template
token is then:

- replaced with a list of rendered tokens if it exactly matches an
  input's ``value-key``;
- substituted in-place if a value-key appears as a substring of a
  larger token (e.g. ``--input=[VALUE]``);
- copied verbatim otherwise.

Rendering rules:

- ``Flag`` inputs emit ``[command-line-flag]`` if true, ``[]`` otherwise.
- Scalars emit ``[value]`` or, with a flag whose separator is whitespace,
  ``[flag, value]``; non-whitespace separators glue flag and value into
  one token (``--input=value``).
- Lists with the default (whitespace) separator emit one token per item
  (each preceded by the flag if present). Custom separators glue items
  into a single token.
- ``SubCommandInput`` / ``SubCommandUnionInput`` recursively resolve the
  nested command-line; the parent flag, if any, prefixes the result.

``simulate()`` wraps :func:`resolve` and joins via :func:`shlex.join` for
human-readable output. ``launch()`` (forthcoming) consumes the token
list directly so we can call ``subprocess.run(..., shell=False)``.
"""

from __future__ import annotations

import shlex
from typing import Any

from boutiques.invocation import invocation_model_for
from boutiques.loader import AnyDescriptor
from boutiques.models.v05.inputs import FlagInput
from boutiques.models.v05_styx.inputs import (
    SubCommandInput,
    SubCommandType,
    SubCommandUnionInput,
)


def resolve(descriptor: AnyDescriptor, invocation: dict[str, Any]) -> list[str]:
    """Validate the invocation and return the resolved argv token list."""
    model_cls = invocation_model_for(descriptor)
    parsed = model_cls.model_validate(invocation)
    values = parsed.model_dump(by_alias=True, exclude_none=True)
    return _resolve_template(descriptor.command_line, descriptor.inputs, values)


def _resolve_template(
    template: str,
    inputs: list | None,
    values: dict[str, Any],
) -> list[str]:
    template_tokens = shlex.split(template)
    inputs = inputs or []
    out: list[str] = []
    for tok in template_tokens:
        out.extend(_expand_token(tok, inputs, values))
    return out


def _expand_token(
    token: str,
    inputs: list,
    values: dict[str, Any],
) -> list[str]:
    # Exact value-key match — render to a token list (possibly empty/multi).
    for inp in inputs:
        vk = getattr(inp, "value_key", None)
        if vk and vk == token:
            return _render_tokens(inp, values.get(inp.id))

    # Embedded value-key — fall back to scalar substitution within the token.
    out = token
    for inp in inputs:
        vk = getattr(inp, "value_key", None)
        if not vk or vk not in out:
            continue
        scalar = _render_scalar_or_empty(inp, values.get(inp.id))
        out = out.replace(vk, scalar)
    return [out] if out else []


def _render_tokens(inp: Any, value: Any) -> list[str]:
    """Render an input value as zero or more argv tokens."""
    if isinstance(inp, SubCommandInput):
        if value is None:
            return []
        nested = _resolve_template(inp.type.command_line, inp.type.inputs, value)
        return _prefix_flag(inp, nested)

    if isinstance(inp, SubCommandUnionInput):
        if value is None:
            return []
        chosen = _choose_subcommand(inp, value)
        nested = _resolve_template(chosen.command_line, chosen.inputs, value)
        return _prefix_flag(inp, nested)

    if value is None:
        return []

    if isinstance(inp, FlagInput):
        return [inp.command_line_flag] if value else []

    if isinstance(value, list):
        sep = inp.list_separator
        if sep is None or sep == " ":
            value_tokens = [str(v) for v in value]
        else:
            value_tokens = [sep.join(str(v) for v in value)]
    else:
        value_tokens = [str(value)]

    return _prefix_flag(inp, value_tokens)


def _prefix_flag(inp: Any, value_tokens: list[str]) -> list[str]:
    """Apply ``command-line-flag`` + ``command-line-flag-separator`` to the value tokens."""
    flag = getattr(inp, "command_line_flag", None)
    if not flag:
        return value_tokens
    sep = getattr(inp, "command_line_flag_separator", None)
    if sep is None or sep == " ":
        return [flag, *value_tokens]
    if not value_tokens:
        return [flag]
    # Non-space separator: glue the flag onto the first value token.
    return [f"{flag}{sep}{value_tokens[0]}", *value_tokens[1:]]


def _render_scalar_or_empty(inp: Any, value: Any) -> str:
    """Render an input as a single scalar string for in-token substitution.

    Used when a value-key appears embedded inside a larger template token
    (e.g. ``--input=[VALUE]``). Multi-token renderings (lists with a
    space separator, sub-commands) collapse to a single space-joined
    string here. The token-level resolver above prefers the exact-match
    path whenever possible.
    """
    if value is None or value is False:
        return ""
    if isinstance(inp, FlagInput):
        return inp.command_line_flag if value else ""
    if isinstance(inp, (SubCommandInput, SubCommandUnionInput)):
        target: SubCommandType
        if isinstance(inp, SubCommandInput):
            target = inp.type
        else:
            target = _choose_subcommand(inp, value)
        return " ".join(_resolve_template(target.command_line, target.inputs, value))
    if isinstance(value, list):
        sep = inp.list_separator if inp.list_separator is not None else " "
        return sep.join(str(v) for v in value)
    return str(value)


def _choose_subcommand(inp: SubCommandUnionInput, value: dict[str, Any]) -> SubCommandType:
    chosen_id = value.get("id")
    for candidate in inp.type:
        if candidate.id == chosen_id:
            return candidate
    raise ValueError(
        f"Invocation for input {inp.id!r} selected sub-command id={chosen_id!r}, "
        f"but no candidate with that id exists."
    )
