"""Runtime backend contract."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunResult:
    """Outcome of a single runtime execution."""

    exit_code: int
    stdout: str
    stderr: str
    duration_seconds: float


class RuntimeError_(RuntimeError):
    """Raised when a runtime can't satisfy a descriptor (e.g. missing image)."""


__all__ = ["RunResult", "RuntimeError_"]
