"""Shared subprocess helper used by every runtime backend.

Spawns a child process and concurrently drains its stdout and stderr in
two threads. Each line is optionally echoed to the parent's stdout/stderr
(streaming) and optionally accumulated into a buffer (capture). Both are
on by default — users get live feedback *and* a ``LaunchResult`` with
the captured output.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import IO

from boutiques.execution.runtime.base import RunResult


def run_subprocess(
    argv: list[str],
    *,
    env: dict[str, str] | None = None,
    cwd: Path | None = None,
    stream: bool = True,
    capture: bool = True,
) -> RunResult:
    """Run ``argv`` as a subprocess; stream and/or capture its output.

    The two threads drain stdout/stderr independently, so neither pipe
    can deadlock on a full kernel buffer.
    """
    full_env = {**os.environ, **(env or {})} if env is not None else None

    proc = subprocess.Popen(
        argv,
        env=full_env,
        cwd=str(cwd) if cwd is not None else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # line-buffered
    )

    stdout_buf: list[str] = []
    stderr_buf: list[str] = []

    out_thread = threading.Thread(
        target=_drain,
        args=(proc.stdout, sys.stdout if stream else None, stdout_buf if capture else None),
    )
    err_thread = threading.Thread(
        target=_drain,
        args=(proc.stderr, sys.stderr if stream else None, stderr_buf if capture else None),
    )

    start = time.monotonic()
    out_thread.start()
    err_thread.start()
    exit_code = proc.wait()
    out_thread.join()
    err_thread.join()
    duration = time.monotonic() - start

    return RunResult(
        exit_code=exit_code,
        stdout="".join(stdout_buf),
        stderr="".join(stderr_buf),
        duration_seconds=duration,
    )


def _drain(
    pipe: IO[str],
    echo_to: IO[str] | None,
    buffer: list[str] | None,
) -> None:
    try:
        for line in iter(pipe.readline, ""):
            if echo_to is not None:
                echo_to.write(line)
                echo_to.flush()
            if buffer is not None:
                buffer.append(line)
    finally:
        pipe.close()
