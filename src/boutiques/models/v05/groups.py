"""v0.5 ``groups`` property: input group constraints."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from boutiques.models.common import IdStr, NonEmptyStr


class Group(BaseModel):
    """An input group with optional mutual-exclusion / one-required / all-or-none rules."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: IdStr = Field(description="Group identifier.")
    name: NonEmptyStr = Field(description="Human-readable name for the input group.")
    description: Optional[str] = Field(
        default=None, description="Description of the input group."
    )
    members: list[IdStr] = Field(
        description="IDs of the inputs belonging to this group.",
        min_length=1,
    )
    mutually_exclusive: bool = Field(
        alias="mutually-exclusive",
        default=False,
        description="Only one input in the group may be active at runtime.",
    )
    one_is_required: bool = Field(
        alias="one-is-required",
        default=False,
        description="At least one input in the group must be active at runtime.",
    )
    all_or_none: bool = Field(
        alias="all-or-none",
        default=False,
        description="Members of the group must be toggled together.",
    )
