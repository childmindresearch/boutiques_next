"""v0.5 ``suggested-resources`` property."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class SuggestedResources(BaseModel):
    """Hints about computational resources needed to run the tool."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    cpu_cores: int | None = Field(
        alias="cpu-cores",
        default=None,
        ge=1,
        description="Requested number of CPU cores.",
    )
    ram: float | None = Field(
        default=None,
        ge=0,
        description="Requested GB of RAM.",
    )
    disk_space: float | None = Field(
        alias="disk-space",
        default=None,
        ge=0,
        description="Requested GB of storage.",
    )
    nodes: int | None = Field(
        default=None,
        ge=1,
        description="Requested number of nodes to spread the application across.",
    )
    walltime_estimate: float | None = Field(
        alias="walltime-estimate",
        default=None,
        ge=0,
        description="Estimated wall time of a task in seconds.",
    )
