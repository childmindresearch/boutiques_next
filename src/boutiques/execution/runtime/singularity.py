"""Singularity / Apptainer runtime."""

from __future__ import annotations

import shutil
from pathlib import Path

from boutiques.execution.runtime._subprocess import run_subprocess
from boutiques.execution.runtime.base import RunResult, RuntimeError_
from boutiques.models.v05.containers import DockerOrSingularityImage, RootfsImage


def run(
    argv: list[str],
    *,
    container_image: object | None,
    env: dict[str, str],
    cwd: Path,
    mounts: list[Path] | None = None,
    runtime_args: list[str] | None = None,
    stream: bool = True,
    capture: bool = True,
) -> RunResult:
    if container_image is None:
        raise RuntimeError_(
            "singularity runtime requires the descriptor to declare a container-image."
        )
    image_uri = _image_uri(container_image)
    binary = _resolve_binary()
    cwd_abs = cwd.resolve()

    wrapper: list[str] = [binary, "exec"]
    for mount in mounts or [cwd_abs]:
        wrapper.extend(["--bind", str(mount)])
    wrapper.extend(["--pwd", str(cwd_abs)])
    for k, v in env.items():
        wrapper.extend(["--env", f"{k}={v}"])
    if runtime_args:
        wrapper.extend(runtime_args)
    wrapper.append(image_uri)
    wrapper.extend(argv)

    return run_subprocess(wrapper, stream=stream, capture=capture)


def _resolve_binary() -> str:
    if shutil.which("apptainer"):
        return "apptainer"
    if shutil.which("singularity"):
        return "singularity"
    return "singularity"  # let subprocess surface a clean FileNotFoundError


def _image_uri(container_image: object) -> str:
    if isinstance(container_image, DockerOrSingularityImage):
        if container_image.index:
            return f"docker://{container_image.index}/{container_image.image}"
        return f"docker://{container_image.image}"
    if isinstance(container_image, RootfsImage):
        return str(container_image.url)
    raise RuntimeError_(f"Unsupported container-image type: {type(container_image).__name__}")
