"""Singularity / Apptainer runtime.

Docker images are pulled via the ``docker://`` URI scheme so users don't
need to build .sif files explicitly. Rootfs images are passed through.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path
from typing import Optional

from boutiques.execution.runtime.base import RunResult, RuntimeError_
from boutiques.models.v05.containers import DockerOrSingularityImage, RootfsImage


def run(
    argv: list[str],
    *,
    container_image: Optional[object],
    env: dict[str, str],
    cwd: Path,
) -> RunResult:
    if container_image is None:
        raise RuntimeError_(
            "singularity runtime requires the descriptor to declare a container-image."
        )
    image_uri = _image_uri(container_image)
    binary = _resolve_binary()

    cwd_abs = cwd.resolve()
    wrapper: list[str] = [
        binary,
        "exec",
        "--bind",
        str(cwd_abs),
        "--pwd",
        str(cwd_abs),
    ]
    for k, v in env.items():
        wrapper.extend(["--env", f"{k}={v}"])
    wrapper.append(image_uri)
    wrapper.extend(argv)

    start = time.monotonic()
    completed = subprocess.run(wrapper, capture_output=True, text=True, check=False)
    return RunResult(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.monotonic() - start,
    )


def _resolve_binary() -> str:
    """Prefer ``apptainer`` if available, fall back to ``singularity``."""
    if shutil.which("apptainer"):
        return "apptainer"
    if shutil.which("singularity"):
        return "singularity"
    return "singularity"  # let subprocess surface a clean FileNotFoundError


def _image_uri(container_image: object) -> str:
    if isinstance(container_image, DockerOrSingularityImage):
        # Pull docker images via the docker:// URI scheme.
        if container_image.index:
            return f"docker://{container_image.index}/{container_image.image}"
        return f"docker://{container_image.image}"
    if isinstance(container_image, RootfsImage):
        return str(container_image.url)
    raise RuntimeError_(f"Unsupported container-image type: {type(container_image).__name__}")
