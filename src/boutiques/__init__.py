"""Boutiques descriptor toolkit."""

from __future__ import annotations

from boutiques._legacy_api import (
    DescriptorValidationError,
    InvocationValidationError,
    execute,
    invocation,
    validate,
)

__version__ = "0.1.0.dev0"

__all__ = [
    "DescriptorValidationError",
    "InvocationValidationError",
    "__version__",
    "execute",
    "invocation",
    "validate",
]
