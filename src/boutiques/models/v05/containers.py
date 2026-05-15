"""v0.5 ``container-image`` property."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from boutiques.models.common import HttpUrlStr, NonEmptyStr


class _BaseContainerImage(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    working_directory: NonEmptyStr | None = Field(
        alias="working-directory",
        default=None,
        description="Location from which the task must be launched inside the container.",
    )
    container_hash: NonEmptyStr | None = Field(
        alias="container-hash",
        default=None,
        description="Hash for the given container.",
    )


class DockerOrSingularityImage(_BaseContainerImage):
    """A docker or singularity image."""

    type: Literal["docker", "singularity"] = Field(description="Container runtime.")
    image: NonEmptyStr = Field(description="Image name. Example: ``bids/mriqc``.")
    entrypoint: bool | None = Field(
        default=None,
        description="True if the container defines an entrypoint.",
    )
    index: NonEmptyStr | None = Field(
        default=None,
        description="Index where the image is available. Example: ``docker.io``.",
    )
    container_opts: list[str] | None = Field(
        alias="container-opts",
        default=None,
        description="Container-level arguments. Example: ``--privileged``.",
    )


class RootfsImage(_BaseContainerImage):
    """A rootfs container image."""

    type: Literal["rootfs"] = Field(description="Container runtime.")
    url: HttpUrlStr = Field(description="URL where the image is available.")


ContainerImage = Annotated[
    DockerOrSingularityImage | RootfsImage,
    Field(discriminator="type"),
]
