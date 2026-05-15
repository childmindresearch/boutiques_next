"""v0.5+styx ``inputs`` property.

Strict superset of v0.5 inputs: keeps String / File / Number / Flag and
adds two new shapes whose ``type`` field is not a literal string:

- ``SubCommandInput``: ``type`` is a ``SubCommandType`` object (hierarchy).
- ``SubCommandUnionInput``: ``type`` is a list of ``SubCommandType`` objects
  (alternation).

Repetition is already expressible in v0.5 via the ``list`` field, so it
needs no new variant.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from boutiques.models.common import IdStr, NonEmptyStr
from boutiques.models.v05.inputs import (
    FileInput as _V05FileInput,
)
from boutiques.models.v05.inputs import (
    FlagInput,
    NumberInput,
    StringInput,
    _BaseInput,
    _ListMixin,
)
from boutiques.models.v05.outputs import Output


class FileInput(_V05FileInput):
    """v0.5+styx FileInput — adds Styx-spec ``mutable`` and ``resolve-parent``."""

    mutable: bool | None = Field(
        default=None,
        description="The tool may modify the input file in place.",
    )
    resolve_parent: bool | None = Field(
        alias="resolve-parent",
        default=None,
        description="The full parent directory of this file must be visible to the tool.",
    )


class SubCommandType(BaseModel):
    """A nested command-line with its own inputs and outputs."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: IdStr = Field(description="Sub-command identifier.")
    name: NonEmptyStr | None = Field(default=None, description="Human-readable name.")
    description: str | None = Field(default=None, description="Sub-command description.")
    command_line: NonEmptyStr = Field(
        alias="command-line",
        description="Command-line template for this sub-command.",
    )
    inputs: list[Input] | None = Field(  # type: ignore[name-defined]
        default=None,
        description="Inputs available within this sub-command.",
    )
    output_files: list[Output] | None = Field(
        alias="output-files",
        default=None,
        description="Outputs produced by this sub-command.",
    )


class SubCommandInput(_BaseInput, _ListMixin):
    """An input whose ``type`` is a single nested ``SubCommandType``."""

    type: SubCommandType


class SubCommandUnionInput(_BaseInput, _ListMixin):
    """An input whose ``type`` is a list of ``SubCommandType`` alternatives."""

    type: list[SubCommandType] = Field(min_length=1)


# Union: the four v0.5 variants plus the two styx variants. Discrimination
# by ``type`` happens naturally — string for v0.5, object for SubCommand,
# list for SubCommandUnion.
Input = StringInput | FileInput | NumberInput | FlagInput | SubCommandInput | SubCommandUnionInput


SubCommandType.model_rebuild()


__all__ = [
    "FileInput",
    "FlagInput",
    "Input",
    "NumberInput",
    "StringInput",
    "SubCommandInput",
    "SubCommandType",
    "SubCommandUnionInput",
]
