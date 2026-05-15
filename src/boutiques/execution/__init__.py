"""Execution engine: bind invocations to descriptors and run them."""

from __future__ import annotations

from typing import Any

from boutiques.execution.resolve import resolve
from boutiques.loader import AnyDescriptor


def simulate(descriptor: AnyDescriptor, invocation: dict[str, Any]) -> str:
    """Return the command-line that ``launch`` would execute."""
    return resolve(descriptor, invocation)


__all__ = ["resolve", "simulate"]
