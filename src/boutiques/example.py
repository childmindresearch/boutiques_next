"""Generate a sample invocation for a descriptor."""

from __future__ import annotations

from typing import Any

from boutiques.invocation import InvocationModelError
from boutiques.loader import AnyDescriptor
from boutiques.models.v05.inputs import FileInput, FlagInput, NumberInput, StringInput
from boutiques.models.v05_styx.inputs import SubCommandInput, SubCommandUnionInput


def generate(descriptor: AnyDescriptor, complete: bool = False) -> dict[str, Any]:
    """Return a sample invocation dict for ``descriptor``.

    By default, required inputs are populated. With ``complete=True``,
    optional inputs are populated as well.
    """
    invocation: dict[str, Any] = {}
    for inp in descriptor.inputs:
        if inp.optional and not complete:
            continue
        invocation[inp.id] = _example_value(inp)
    return invocation


def _example_value(inp: Any) -> Any:
    if isinstance(inp, (SubCommandInput, SubCommandUnionInput)):
        raise InvocationModelError(
            f"Example generation does not yet support sub-command inputs "
            f"(input id={inp.id!r})."
        )

    base = _scalar_example(inp)
    if getattr(inp, "list_", False):
        min_entries = int(inp.min_list_entries) if inp.min_list_entries else 1
        return [base] * max(1, min_entries)
    return base


def _scalar_example(inp: Any) -> Any:
    if inp.default_value is not None:
        return inp.default_value
    choices = getattr(inp, "value_choices", None)
    if choices:
        return choices[0]
    if isinstance(inp, FlagInput):
        return True
    if isinstance(inp, NumberInput):
        if inp.minimum is not None:
            return int(inp.minimum) if inp.integer else float(inp.minimum)
        return 0 if inp.integer else 0.0
    if isinstance(inp, FileInput):
        return f"/path/to/{inp.id}"
    if isinstance(inp, StringInput):
        return f"example_{inp.id}"
    return f"example_{inp.id}"
