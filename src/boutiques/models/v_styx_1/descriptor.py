"""v0.5+styx Descriptor: a strict superset of v0.5."""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from boutiques.models.common import HttpUrlStr, NonEmptyStr
from boutiques.models.v_0_5.containers import ContainerImage
from boutiques.models.v_0_5.environment import EnvironmentVariable
from boutiques.models.v_0_5.errors import ErrorCode
from boutiques.models.v_0_5.groups import Group
from boutiques.models.v_0_5.outputs import Output
from boutiques.models.v_0_5.resources import SuggestedResources
from boutiques.models.v_0_5.tests import TestCase
from boutiques.models.v_styx_1.inputs import Input

TagValue = Union[str, list[str], bool]


class Descriptor(BaseModel):
    """A complete Boutiques 0.5+styx descriptor.

    Field-compatible with v0.5 except for the ``schema-version`` literal
    and the broader ``inputs`` union (which admits SubCommand variants).
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    # Required
    name: NonEmptyStr = Field(description="Tool name.")
    description: NonEmptyStr = Field(description="Tool description.")
    tool_version: NonEmptyStr = Field(alias="tool-version", description="Tool version.")
    command_line: NonEmptyStr = Field(alias="command-line", description="Command-line template.")
    schema_version: Literal["0.5+styx"] = Field(alias="schema-version")
    inputs: list[Input] = Field(min_length=1)

    # Optional metadata
    author: Optional[NonEmptyStr] = Field(default=None)
    url: Optional[HttpUrlStr] = Field(default=None)
    descriptor_url: Optional[HttpUrlStr] = Field(alias="descriptor-url", default=None)
    doi: Optional[NonEmptyStr] = Field(default=None)
    tool_doi: Optional[NonEmptyStr] = Field(alias="tool-doi", default=None)
    deprecated_by_doi: Optional[Union[NonEmptyStr, bool]] = Field(
        alias="deprecated-by-doi", default=None
    )
    online_platform_urls: Optional[list[HttpUrlStr]] = Field(
        alias="online-platform-urls", default=None
    )
    shell: Optional[NonEmptyStr] = Field(default=None)

    # Optional execution
    container_image: Optional[ContainerImage] = Field(
        alias="container-image", default=None
    )
    environment_variables: Optional[list[EnvironmentVariable]] = Field(
        alias="environment-variables", default=None, min_length=1
    )
    groups: Optional[list[Group]] = Field(default=None, min_length=1)
    output_files: Optional[list[Output]] = Field(
        alias="output-files", default=None, min_length=1
    )
    suggested_resources: Optional[SuggestedResources] = Field(
        alias="suggested-resources", default=None
    )
    error_codes: Optional[list[ErrorCode]] = Field(
        alias="error-codes", default=None, min_length=1
    )

    # Optional auxiliary
    tests: Optional[list[TestCase]] = Field(default=None, min_length=1)
    tags: Optional[dict[str, TagValue]] = Field(default=None)
    invocation_schema: Optional[dict[str, Any]] = Field(
        alias="invocation-schema", default=None
    )
    custom: Optional[dict[str, Any]] = Field(default=None)


Descriptor.model_rebuild()


__all__ = ["Descriptor"]


DescriptorVStyx1 = Annotated[Descriptor, Field(description="Boutiques 0.5+styx descriptor.")]
