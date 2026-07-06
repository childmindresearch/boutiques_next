"""Backward-compatible shims for the classic ``boutiques`` Python API.

Classic ``boutiques`` exposes module-level functions that *raise* on failure
(``validate``, ``invocation``, ``execute``) plus the exception types
``DescriptorValidationError`` / ``InvocationValidationError``. Downstream tools
(e.g. Nipoppy) import these directly:

    boutiques.validate(descriptor_str)               # raises on invalid
    boutiques.invocation("--invocation", inv, desc)  # raises on invalid

We re-expose the same names with compatible behavior so those callers keep
working. Signatures mirror classic's argv-style ``*params`` because that is
how downstream code invokes them.
"""

from __future__ import annotations

from typing import Any

# Re-export under the classic name; classic raises this on invalid invocations.
from boutiques.invocation_check import InvocationValidationError as InvocationValidationError
from boutiques.invocation_check import validate_invocation
from boutiques.loader import load, read_json
from boutiques.validate import validate as _validate_descriptor

ISSUE_URL = "https://github.com/childmindresearch/boutiques_next/issues"

_INVOCATION_FLAGS = frozenset({"-i", "--invocation", "--input"})


class DescriptorValidationError(Exception):
    """Raised when a descriptor fails validation (classic-compatible name)."""


def validate(*params: str) -> str:
    """Validate a descriptor. Classic-compatible: raises on invalid.

    The descriptor (path, http(s) URL, or JSON string) is the first
    positional argument. Extra classic flags (``--bids``, ``--format``,
    ``--sandbox``, ...) are accepted and ignored where unsupported.
    """
    descriptor = _first_positional(params)
    result = _validate_descriptor(descriptor)
    if not result.ok:
        raise DescriptorValidationError(result.format())
    return "OK"


def invocation(*params: str) -> str:
    """Validate an invocation against a descriptor. Classic-compatible.

    Mirrors classic argv-style usage: a positional descriptor plus the
    invocation via ``-i``/``--invocation``. Raises
    :class:`DescriptorValidationError` if the descriptor is invalid, or
    :class:`InvocationValidationError` if the invocation is invalid.
    """
    descriptor_src, invocation_src = _parse_invocation_params(params)
    validate(descriptor_src)  # classic validates the descriptor first
    if invocation_src is None:
        return "OK"
    descriptor = load(descriptor_src)
    errors = validate_invocation(descriptor, read_json(invocation_src))
    if errors:
        raise InvocationValidationError(errors)
    return "OK"


def execute(*params: str) -> Any:
    """Classic ``boutiques.execute`` — not implemented in this runtime yet."""
    raise NotImplementedError(
        "boutiques.execute() is not implemented in this runtime yet. "
        f"Use the `bosh exec` CLI, or open an issue at {ISSUE_URL}."
    )


def _first_positional(params: tuple[str, ...]) -> str:
    for tok in params:
        if not str(tok).startswith("-"):
            return tok
    raise DescriptorValidationError("No descriptor argument was provided.")


def _parse_invocation_params(params: tuple[str, ...]) -> tuple[str, str | None]:
    """Split classic argv-style params into (descriptor, invocation-or-None).

    Handles both orders classic accepts, e.g. ``(desc, "-i", inv)`` and
    ``("--invocation", inv, desc)``. Unknown flags are skipped.
    """
    positionals: list[str] = []
    invocation_src: str | None = None
    i = 0
    while i < len(params):
        tok = params[i]
        if tok in _INVOCATION_FLAGS:
            invocation_src = params[i + 1] if i + 1 < len(params) else None
            i += 2
            continue
        if str(tok).startswith("-"):
            i += 1  # unrelated flag (e.g. --sandbox, --write-schema); ignore
            continue
        positionals.append(tok)
        i += 1
    if not positionals:
        raise DescriptorValidationError("No descriptor argument was provided.")
    return positionals[0], invocation_src
