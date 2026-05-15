"""v0.5+styx ``stdout-output`` / ``stderr-output`` declarations.

These declare the tool's stdout (or stderr) as a named output. They
have no ``path-template`` because the captured text is the output — the
runtime fills it in after the run.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from boutiques.models.common import IdStr, NonEmptyStr


class StdoutOutput(BaseModel):
    """Declare the tool's stdout as a named output."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: IdStr = Field(description="Output identifier.")
    name: NonEmptyStr | None = Field(default=None, description="Human-readable name.")
    description: str | None = Field(default=None, description="Output description.")


class StderrOutput(StdoutOutput):
    """Declare the tool's stderr as a named output."""
