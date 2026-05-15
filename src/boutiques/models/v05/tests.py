"""v0.5 ``tests`` property."""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from boutiques.models.common import IdStr, NonEmptyStr


class _OutputAssertion(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: IdStr = Field(description="ID referring to an output-file.")
    md5_reference: Optional[NonEmptyStr] = Field(
        alias="md5-reference",
        default=None,
        description="MD5 checksum to match against the produced output.",
    )


class TestAssertions(BaseModel):
    """Assertions about a tool run.

    At least one of ``exit-code`` or ``output-files`` must be provided.
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    exit_code: Optional[int] = Field(
        alias="exit-code",
        default=None,
        description="Expected exit code.",
    )
    output_files: Optional[list[_OutputAssertion]] = Field(
        alias="output-files",
        default=None,
        min_length=1,
    )

    @model_validator(mode="after")
    def _at_least_one(self) -> "TestAssertions":
        if self.exit_code is None and self.output_files is None:
            raise ValueError(
                "Test assertions must specify at least one of 'exit-code' or 'output-files'."
            )
        return self


class TestCase(BaseModel):
    """A named test case bound to a sample invocation."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    name: NonEmptyStr = Field(description="Test case name.")
    invocation: dict[str, Any] = Field(description="Sample invocation used by the test.")
    assertions: TestAssertions = Field(description="Assertions to evaluate after the run.")
