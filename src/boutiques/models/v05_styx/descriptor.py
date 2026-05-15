"""v0.5+styx Descriptor: a strict superset of v0.5."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from boutiques.models.common import HttpUrlStr, NonEmptyStr
from boutiques.models.v05.containers import ContainerImage
from boutiques.models.v05.environment import EnvironmentVariable
from boutiques.models.v05.errors import ErrorCode
from boutiques.models.v05.groups import Group
from boutiques.models.v05.outputs import Output
from boutiques.models.v05.resources import SuggestedResources
from boutiques.models.v05.tests import TestCase
from boutiques.models.v05_styx.inputs import Input

TagValue = str | list[str] | bool


class Descriptor(BaseModel):
    """A complete Boutiques 0.5+styx descriptor.

    Field-compatible with v0.5 except for the ``schema-version`` literal
    and the broader ``inputs`` union (which admits SubCommand variants).
    """

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    # Required
    name: NonEmptyStr = Field(description="Tool name.")
    description: NonEmptyStr = Field(description="Tool description.")
    command_line: NonEmptyStr = Field(alias="command-line", description="Command-line template.")
    schema_version: Literal["0.5+styx"] = Field(alias="schema-version")
    inputs: list[Input] = Field(min_length=1)

    # Recommended (lint warns when absent) but not required by v0.5+styx, since
    # niwrap-style descriptors carry version metadata in sidecar packaging.
    tool_version: NonEmptyStr | None = Field(
        alias="tool-version", default=None, description="Tool version."
    )

    # Optional metadata
    author: NonEmptyStr | None = Field(default=None)
    url: HttpUrlStr | None = Field(default=None)
    descriptor_url: HttpUrlStr | None = Field(alias="descriptor-url", default=None)
    doi: NonEmptyStr | None = Field(default=None)
    tool_doi: NonEmptyStr | None = Field(alias="tool-doi", default=None)
    deprecated_by_doi: NonEmptyStr | bool | None = Field(alias="deprecated-by-doi", default=None)
    online_platform_urls: list[HttpUrlStr] | None = Field(
        alias="online-platform-urls", default=None
    )
    shell: NonEmptyStr | None = Field(default=None)

    # Optional execution
    container_image: ContainerImage | None = Field(alias="container-image", default=None)
    environment_variables: list[EnvironmentVariable] | None = Field(
        alias="environment-variables", default=None, min_length=1
    )
    groups: list[Group] | None = Field(default=None, min_length=1)
    output_files: list[Output] | None = Field(alias="output-files", default=None, min_length=1)
    suggested_resources: SuggestedResources | None = Field(
        alias="suggested-resources", default=None
    )
    error_codes: list[ErrorCode] | None = Field(alias="error-codes", default=None, min_length=1)

    # Optional auxiliary
    tests: list[TestCase] | None = Field(default=None, min_length=1)
    tags: dict[str, TagValue] | None = Field(default=None)
    invocation_schema: dict[str, Any] | None = Field(alias="invocation-schema", default=None)
    custom: dict[str, Any] | None = Field(default=None)


Descriptor.model_rebuild()


__all__ = ["Descriptor"]
