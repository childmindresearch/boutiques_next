"""Local runtime: run the resolved argv directly via :mod:`subprocess`."""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path
from typing import Optional

from boutiques.execution.runtime.base import RunResult


def run(
    argv: list[str],
    *,
    container_image: Optional[object] = None,  # ignored
    env: dict[str, str],
    cwd: Path,
) -> RunResult:
    """Run ``argv`` in a subprocess and capture stdout/stderr."""
    full_env = {**os.environ, **env}
    start = time.monotonic()
    completed = subprocess.run(
        argv,
        cwd=str(cwd),
        env=full_env,
        capture_output=True,
        text=True,
        check=False,
    )
    return RunResult(
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        duration_seconds=time.monotonic() - start,
    )
