"""Local runtime: run the resolved argv directly via :mod:`subprocess`."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from boutiques.execution.runtime._subprocess import run_subprocess
from boutiques.execution.runtime.base import RunResult


def run(
    argv: list[str],
    *,
    container_image: Optional[object] = None,  # ignored
    env: dict[str, str],
    cwd: Path,
    mounts: Optional[list[Path]] = None,  # ignored
    runtime_args: Optional[list[str]] = None,  # ignored
    stream: bool = True,
    capture: bool = True,
) -> RunResult:
    """Run ``argv`` locally; stream/capture per the flags."""
    return run_subprocess(argv, env=env, cwd=cwd, stream=stream, capture=capture)
