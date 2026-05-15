"""Field types and base classes shared across schema versions."""

from __future__ import annotations

from typing import Annotated

from pydantic import StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
"""Non-empty string (matches the v0.5 ``minLength: 1`` constraint)."""

IdStr = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9_a-zA-Z]+$", min_length=1),
]
"""Identifier: alphanumeric + underscore, at least one character."""

EnvVarName = Annotated[
    str,
    StringConstraints(pattern=r"^[a-zA-Z][0-9_a-zA-Z]*$", min_length=1),
]
"""Environment variable name: must start with a letter."""

HttpUrlStr = Annotated[str, StringConstraints(pattern=r"^https?://")]
"""URL as a plain string. Matches the v0.5 schema's pattern check rather
than ``pydantic.HttpUrl`` to keep real-world descriptors loadable.
"""
