"""Docker runtime: wrap the argv in a ``docker run`` invocation.

Mounts the current working directory into the container at the same path
and runs the tool's argv there. Pulls the image on-demand via docker's
default behavior.
"""

from __future__ import annotations

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
            "docker runtime requires the descriptor to declare a container-image."
        )
    image_ref = _image_ref(container_image)

    cwd_abs = cwd.resolve()
    wrapper: list[str] = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{cwd_abs}:{cwd_abs}",
        "-w",
        str(cwd_abs),
    ]
    for k, v in env.items():
        wrapper.extend(["-e", f"{k}={v}"])
    if isinstance(container_image, DockerOrSingularityImage) and container_image.container_opts:
        wrapper.extend(container_image.container_opts)
    wrapper.append(image_ref)
    wrapper.extend(argv)

    start = time.monotonic()
    completed = subprocess.run(wrapper, capture_output=True, text=True, check=False)
    return RunResult(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.monotonic() - start,
    )


def _image_ref(container_image: object) -> str:
    if isinstance(container_image, DockerOrSingularityImage):
        if container_image.index:
            return f"{container_image.index}/{container_image.image}"
        return container_image.image
    if isinstance(container_image, RootfsImage):
        raise RuntimeError_(
            "docker runtime cannot launch a rootfs-type container image. "
            "Use the singularity runtime instead."
        )
    raise RuntimeError_(f"Unsupported container-image type: {type(container_image).__name__}")
