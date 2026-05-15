"""v0.5 ``output-files`` property."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from boutiques.models.common import IdStr, NonEmptyStr


class Output(BaseModel):
    """A declared output file.

    Exactly one of ``path-template`` or ``conditional-path-template`` must
    be set, per the v0.5 spec.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: IdStr = Field(description="Output identifier.")
    name: NonEmptyStr = Field(description="Human-readable output name.")
    description: Optional[str] = Field(default=None, description="Output description.")
    optional: bool = Field(default=False, description="True if the output may not be produced.")

    path_template: Optional[NonEmptyStr] = Field(
        alias="path-template",
        default=None,
        description="Output path relative to the execution directory; may contain value keys.",
    )
    conditional_path_template: Optional[list[dict[str, str]]] = Field(
        alias="conditional-path-template",
        default=None,
        min_length=1,
        description=(
            "List of single-entry objects mapping a boolean expression to an output "
            "path. The first matching expression wins; ``default`` is the fallback."
        ),
    )
    path_template_stripped_extensions: Optional[list[str]] = Field(
        alias="path-template-stripped-extensions",
        default=None,
        description="Extensions stripped from input values before substituting into the template.",
    )

    list_: Optional[bool] = Field(
        alias="list",
        default=None,
        description="True if the output is a list of values.",
    )
    command_line_flag: Optional[str] = Field(
        alias="command-line-flag",
        default=None,
        description="Option flag preceding the output value at substitution time.",
    )
    command_line_flag_separator: Optional[str] = Field(
        alias="command-line-flag-separator", default=None
    )
    value_key: Optional[str] = Field(alias="value-key", default=None)
    uses_absolute_path: Optional[bool] = Field(
        alias="uses-absolute-path",
        default=None,
        description="Output filepath will be given as an absolute path.",
    )
    file_template: Optional[list[NonEmptyStr]] = Field(
        alias="file-template",
        default=None,
        min_length=1,
        description="Lines (with value keys) written to a generated configuration file.",
    )

    @model_validator(mode="after")
    def _exactly_one_path_template(self) -> "Output":
        has_path = self.path_template is not None
        has_cond = self.conditional_path_template is not None
        if has_path == has_cond:
            raise ValueError(
                "Output must declare exactly one of 'path-template' or "
                "'conditional-path-template'."
            )
        return self
