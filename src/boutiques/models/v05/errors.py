"""v0.5 ``error-codes`` property."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ErrorCode(BaseModel):
    """An exit code value and its meaning."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    code: int = Field(description="Value of the exit code.")
    description: str = Field(description="Description of the error code.")
