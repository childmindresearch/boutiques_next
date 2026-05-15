"""Soft advisories for descriptors that load successfully.

Lint covers the "recommended but not required" tier: a descriptor that
parses cleanly may still be missing fields that make it portable or
self-contained. Each ``LintIssue`` is informational — it does not block
validation or execution.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from boutiques.loader import AnyDescriptor
from boutiques.models.v05 import Descriptor as V05Descriptor
from boutiques.models.v05_styx import Descriptor as V05StyxDescriptor


@dataclass
class LintIssue:
    """A non-blocking advisory about a descriptor."""

    field: str
    message: str
    level: str = "warning"

    def __str__(self) -> str:
        if self.field:
            return f"[{self.level}] {self.field}: {self.message}"
        return f"[{self.level}] {self.message}"


def _recommend_tool_version(d: AnyDescriptor) -> list[LintIssue]:
    if isinstance(d, V05StyxDescriptor) and d.tool_version is None:
        return [
            LintIssue(
                field="tool-version",
                message=(
                    "Recommended: declare tool-version so the descriptor is "
                    "self-contained outside of any packaging metadata."
                ),
            )
        ]
    return []


def _recommend_container_image(d: AnyDescriptor) -> list[LintIssue]:
    if d.container_image is None:
        return [
            LintIssue(
                field="container-image",
                message=(
                    "Recommended: declare a container-image so the tool can be "
                    "launched reproducibly without external configuration."
                ),
            )
        ]
    return []


_RECOMMENDATIONS: list[Callable[[AnyDescriptor], list[LintIssue]]] = [
    _recommend_tool_version,
    _recommend_container_image,
]


def lint(descriptor: AnyDescriptor) -> list[LintIssue]:
    """Return advisory issues for a successfully loaded descriptor."""
    issues: list[LintIssue] = []
    for check in _RECOMMENDATIONS:
        issues.extend(check(descriptor))
    return issues


# Silence unused-import warning when V05Descriptor isn't referenced by checks yet.
_ = V05Descriptor
