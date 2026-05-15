"""Validate a Boutiques descriptor.

``validate`` runs three tiers in order:

1. **Structural** — Pydantic parsing. Failure = hard error.
2. **Semantic** (cross-field) — from :mod:`boutiques.semantic`. Failure
   = hard error.
3. **Lint** — soft advisories from :mod:`boutiques.lint`. Never blocks.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from boutiques._errors import ValidationError
from boutiques.lint import LintIssue, lint
from boutiques.loader import AnyDescriptor, DescriptorLoadError, load
from boutiques.semantic import check as _semantic_check

__all__ = ["ValidationError", "ValidationResult", "validate"]


@dataclass
class ValidationResult:
    """Outcome of validating a descriptor."""

    descriptor: AnyDescriptor | None = None
    errors: list[ValidationError] = field(default_factory=list)
    warnings: list[LintIssue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """True if there are no hard errors. Warnings do not affect this."""
        return not self.errors

    def format(self) -> str:
        if not self.ok:
            return "\n".join(str(e) for e in self.errors)
        if self.warnings:
            return "OK with warnings:\n" + "\n".join(str(w) for w in self.warnings)
        return "OK"


def validate(source: str | Path | dict[str, Any]) -> ValidationResult:
    """Validate a descriptor and return a ``ValidationResult``."""
    try:
        descriptor = load(source)
    except DescriptorLoadError as exc:
        return ValidationResult(errors=_parse_pydantic_message(str(exc)))

    semantic_errors = _semantic_check(descriptor)
    if semantic_errors:
        return ValidationResult(descriptor=descriptor, errors=semantic_errors)

    warnings = lint(descriptor)
    return ValidationResult(descriptor=descriptor, warnings=warnings)


def _parse_pydantic_message(message: str) -> list[ValidationError]:
    """Turn Pydantic's multi-line error dump into a list of ``ValidationError``."""
    errors: list[ValidationError] = []
    lines = [line.rstrip() for line in message.splitlines() if line.strip()]
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
