"""Execution engine: bind invocations to descriptors and run them."""

from __future__ import annotations

import shlex
from typing import Any

from boutiques.execution.launch import LaunchResult, launch
from boutiques.execution.resolve import resolve
from boutiques.loader import AnyDescriptor


def simulate(descriptor: AnyDescriptor, invocation: dict[str, Any]) -> str:
    """Return the resolved command-line as a shell-safe string."""
    return shlex.join(resolve(descriptor, invocation))


__all__ = ["LaunchResult", "launch", "resolve", "simulate"]
