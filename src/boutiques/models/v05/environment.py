"""v0.5 ``environment-variables`` property."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from boutiques.models.common import EnvVarName


class EnvironmentVariable(BaseModel):
    """A name/value pair set in the execution environment."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    name: EnvVarName = Field(description="Environment variable name.")
    value: str = Field(description="Value of the environment variable.")
    description: str | None = Field(
        default=None, description="Description of the environment variable."
    )
