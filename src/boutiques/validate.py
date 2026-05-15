"""Validate a Boutiques descriptor.

For now, ``validate`` is a thin wrapper over the Pydantic model: it returns
a ``ValidationResult`` with the structural errors collected by Pydantic.
Cross-field semantic checks (e.g. ``min-list-entries`` only when
``list: true``) will land here as they are added.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union

from boutiques.loader import AnyDescriptor, DescriptorLoadError, load


@dataclass
class ValidationError:
    """A single validation failure with a JSON-pointer-style location."""

    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.location}: {self.message}" if self.location else self.message


@dataclass
class ValidationResult:
    """Outcome of validating a descriptor."""

    descriptor: Union[AnyDescriptor, None] = None
    errors: list[ValidationError] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors

    def format(self) -> str:
        if self.ok:
            return "OK"
        return "\n".join(str(e) for e in self.errors)


def validate(source: Union[str, Path, dict[str, Any]]) -> ValidationResult:
    """Validate a descriptor and return a ``ValidationResult``."""
    try:
        descriptor = load(source)
    except DescriptorLoadError as exc:
        return ValidationResult(errors=_parse_pydantic_message(str(exc)))
    return ValidationResult(descriptor=descriptor)


def _parse_pydantic_message(message: str) -> list[ValidationError]:
    """Turn Pydantic's multi-line error dump into a list of ``ValidationError``.

    Pydantic 2's default ``str(ValidationError)`` formats each error as
    ``<location>\\n  <message> [type=...]``. We keep that structure.
    """
    errors: list[ValidationError] = []
    lines = [line.rstrip() for line in message.splitlines() if line.strip()]
    # First line is the summary ("N validation errors for Descriptor"). Skip it.
    body = lines[1:] if lines and "validation error" in lines[0] else lines
    i = 0
    while i < len(body):
        location = body[i]
        msg = body[i + 1].strip() if i + 1 < len(body) else ""
        errors.append(ValidationError(location=location, message=msg))
        i += 2
    if not errors:
        errors.append(ValidationError(location="", message=message))
    return errors
