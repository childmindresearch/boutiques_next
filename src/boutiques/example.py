"""Generate a sample invocation for a descriptor."""

from __future__ import annotations

from typing import Any

from boutiques.invocation import DISCRIMINATOR_KEY
from boutiques.loader import AnyDescriptor
from boutiques.models.v05.inputs import FileInput, FlagInput, NumberInput, StringInput
from boutiques.models.v05_styx.inputs import (
    SubCommandInput,
    SubCommandType,
    SubCommandUnionInput,
)


def generate(descriptor: AnyDescriptor, complete: bool = False) -> dict[str, Any]:
    """Return a sample invocation dict for ``descriptor``.

    By default, required inputs are populated. With ``complete=True``,
    optional inputs are populated as well. Sub-command unions pick the
    first candidate.

    ``Flag`` inputs are treated as effectively optional regardless of
    their declared ``optional`` field — at the runtime layer a flag's
    absence and value=false are indistinguishable, so a minimum
    invocation omits all flags. (This matches the v0.5+styx spec
    author's note that ``optional`` has no meaning for Flag inputs.)
    """
    return _generate(descriptor, complete=complete)


def _generate(
    target: AnyDescriptor | SubCommandType,
    complete: bool,
) -> dict[str, Any]:
    invocation: dict[str, Any] = {}
    for inp in target.inputs or []:
        if not complete:
            if inp.optional:
                continue
            if isinstance(inp, FlagInput):
                continue
        invocation[inp.id] = _example_value(inp, complete=complete)
    return invocation


def _example_value(inp: Any, complete: bool) -> Any:
    if isinstance(inp, SubCommandInput):
        return _generate(inp.type, complete=complete)
    if isinstance(inp, SubCommandUnionInput):
        chosen = inp.type[0]
        return {DISCRIMINATOR_KEY: chosen.id, **_generate(chosen, complete=complete)}

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
