"""v0.5 ``output-files`` property."""

from __future__ import annotations

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
    description: str | None = Field(default=None, description="Output description.")
    optional: bool = Field(default=False, description="True if the output may not be produced.")

    path_template: NonEmptyStr | None = Field(
        alias="path-template",
        default=None,
        description="Output path relative to the execution directory; may contain value keys.",
    )
    conditional_path_template: list[dict[str, str]] | None = Field(
        alias="conditional-path-template",
        default=None,
        min_length=1,
        description=(
            "List of single-entry objects mapping a boolean expression to an output "
            "path. The first matching expression wins; ``default`` is the fallback."
        ),
    )
    path_template_stripped_extensions: list[str] | None = Field(
        alias="path-template-stripped-extensions",
        default=None,
        description="Extensions stripped from input values before substituting into the template.",
    )

    list_: bool | None = Field(
        alias="list",
        default=None,
        description="True if the output is a list of values.",
    )
    command_line_flag: str | None = Field(
        alias="command-line-flag",
        default=None,
        description="Option flag preceding the output value at substitution time.",
    )
    command_line_flag_separator: str | None = Field(
        alias="command-line-flag-separator", default=None
    )
    value_key: str | None = Field(alias="value-key", default=None)
    uses_absolute_path: bool | None = Field(
        alias="uses-absolute-path",
        default=None,
        description="Output filepath will be given as an absolute path.",
    )
    file_template: list[NonEmptyStr] | None = Field(
        alias="file-template",
        default=None,
        min_length=1,
        description="Lines (with value keys) written to a generated configuration file.",
    )

    @model_validator(mode="after")
    def _exactly_one_path_template(self) -> Output:
        has_path = self.path_template is not None
        has_cond = self.conditional_path_template is not None
        if has_path == has_cond:
            raise ValueError(
                "Output must declare exactly one of 'path-template' or 'conditional-path-template'."
            )
        return self
