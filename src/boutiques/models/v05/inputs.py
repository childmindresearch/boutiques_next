"""v0.5 ``inputs`` property.

Modelled as four input variants — String, File, Number, Flag — each
optionally a list and optionally flagged. Cross-field constraints (e.g.
``min-list-entries`` only when ``list: true``) are enforced in
``boutiques.validate``, not here, to keep the structural model simple.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from boutiques.models.common import IdStr, NonEmptyStr


class _BaseInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: IdStr = Field(description="Input identifier.")
    name: NonEmptyStr = Field(description="Human-readable name.")
    description: str | None = Field(default=None, description="Input description.")
    value_key: str | None = Field(
        alias="value-key",
        default=None,
        description="Token in command-line substituted at runtime.",
    )
    optional: bool = Field(default=False, description="True if optional.")
    requires_inputs: list[str] | None = Field(
        alias="requires-inputs",
        default=None,
        description="IDs of inputs or groups that must be active for this input to be available.",
    )
    disables_inputs: list[str] | None = Field(
        alias="disables-inputs",
        default=None,
        description="IDs of inputs that are disabled when this input is active.",
    )
    value_requires: dict[str, list[str]] | None = Field(
        alias="value-requires",
        default=None,
        description="Per-choice IDs of inputs required when that value is selected.",
    )
    value_disables: dict[str, list[str]] | None = Field(
        alias="value-disables",
        default=None,
        description="Per-choice IDs of inputs disabled when that value is selected.",
    )

    command_line_flag: str | None = Field(
        alias="command-line-flag",
        default=None,
        description="Option flag preceding the value at substitution time.",
    )
    command_line_flag_separator: str | None = Field(
        alias="command-line-flag-separator",
        default=None,
        description="Separator between flag and value. Defaults to a single space.",
    )


class _ListMixin(BaseModel):
    list_: bool | None = Field(
        alias="list",
        default=None,
        description="True if the input is a list of values.",
    )
    list_separator: str | None = Field(
        alias="list-separator",
        default=None,
        description="Separator between list items. Defaults to a single space.",
    )
    min_list_entries: float | None = Field(
        alias="min-list-entries",
        default=None,
        description="Minimum number of list entries.",
    )
    max_list_entries: float | None = Field(
        alias="max-list-entries",
        default=None,
        description="Maximum number of list entries.",
    )


class StringInput(_BaseInput, _ListMixin):
    """String-typed input."""

    type: Literal["String"]
    default_value: str | list[str] | None = Field(alias="default-value", default=None)
    value_choices: list[str] | None = Field(alias="value-choices", default=None)


class FileInput(_BaseInput, _ListMixin):
    """File-typed input."""

    type: Literal["File"]
    default_value: str | list[str] | None = Field(alias="default-value", default=None)
    uses_absolute_path: bool | None = Field(
        alias="uses-absolute-path",
        default=None,
        description="Value must be given as an absolute path.",
    )


class NumberInput(_BaseInput, _ListMixin):
    """Number-typed input (integer or float, controlled by ``integer``)."""

    type: Literal["Number"]
    integer: bool | None = Field(
        default=None,
        description="True if the value must be an integer.",
    )
    minimum: float | None = Field(default=None, description="Inclusive minimum.")
    maximum: float | None = Field(default=None, description="Inclusive maximum.")
    exclusive_minimum: bool | None = Field(alias="exclusive-minimum", default=None)
    exclusive_maximum: bool | None = Field(alias="exclusive-maximum", default=None)
    default_value: float | list[float] | None = Field(alias="default-value", default=None)
    value_choices: list[float] | None = Field(alias="value-choices", default=None)


class FlagInput(_BaseInput):
    """Boolean flag input. Always carries a command-line flag."""

    type: Literal["Flag"]
    command_line_flag: str = Field(  # type: ignore[assignment]
        alias="command-line-flag",
        description="Option flag emitted when the flag is set.",
    )
    default_value: bool | None = Field(alias="default-value", default=None)


Input = Annotated[
    StringInput | FileInput | NumberInput | FlagInput,
    Field(discriminator="type"),
]


__all__ = [
    "FileInput",
    "FlagInput",
    "Input",
    "NumberInput",
    "StringInput",
]


# Allow downstream code (e.g. ``Any`` annotations) without f-importing unused names.
_ = Any
