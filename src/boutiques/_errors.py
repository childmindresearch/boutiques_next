"""Shared error dataclass for validation errors.

Lives in its own module so both :mod:`boutiques.validate` and
:mod:`boutiques.semantic` can import it without circularity.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ValidationError:
    """A single validation failure with a JSON-pointer-style location."""

    location: str
    message: str

    def __str__(self) -> str:
        return f"{self.location}: {self.message}" if self.location else self.message
