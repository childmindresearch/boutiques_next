"""Validate a concrete invocation against a descriptor.

Three layers run in sequence; the first failing layer short-circuits:

1. **Structural** — the dynamic Pydantic model from
   :mod:`boutiques.invocation`. Enforces types, choices (via
   ``Literal``), numeric ranges, and list bounds.
2. **Cross-input** — ``requires-inputs``, ``disables-inputs``,
   ``value-requires``, ``value-disables``. Recurses through
   sub-commands.
3. **Group constraints** — ``mutually-exclusive``, ``one-is-required``,
   ``all-or-none`` on the top-level descriptor's ``groups`` array.

Use :func:`validate_invocation` from library code; the resolver wraps
it and raises :class:`InvocationValidationError` on any failure.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError as PydanticValidationError

from boutiques._errors import ValidationError
from boutiques.invocation import DISCRIMINATOR_KEY, invocation_model_for
from boutiques.loader import AnyDescriptor
from boutiques.models.v05.inputs import FlagInput
from boutiques.models.v05_styx.inputs import (
    SubCommandInput,
    SubCommandType,
    SubCommandUnionInput,
)


class InvocationValidationError(Exception):
    """Raised when an invocation fails any of the validation tiers."""

    def __init__(self, errors: list[ValidationError]) -> None:
        self.errors = errors
        super().__init__("\n".join(str(e) for e in errors) or "Invocation validation failed.")


def validate_invocation(
    descriptor: AnyDescriptor,
    invocation: dict[str, Any],
) -> list[ValidationError]:
    """Validate ``invocation`` against ``descriptor``; return every error found."""
    errors: list[ValidationError] = []

    model_cls = invocation_model_for(descriptor)
    try:
        parsed = model_cls.model_validate(invocation)
    except PydanticValidationError as exc:
        errors.extend(_pydantic_to_validation_errors(exc))
        return errors

    values = parsed.model_dump(by_alias=True, exclude_none=True)
    _check_scope(descriptor, values, errors, prefix="")
    errors.extend(_check_groups(descriptor, values))
    return errors


# ---------------------------------------------------------------------------
# Pydantic → ValidationError adapter
# ---------------------------------------------------------------------------


def _pydantic_to_validation_errors(exc: PydanticValidationError) -> list[ValidationError]:
    out: list[ValidationError] = []
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"])
        out.append(ValidationError(location=loc, message=err["msg"]))
    return out


# ---------------------------------------------------------------------------
# Scope walker
# ---------------------------------------------------------------------------


def _check_scope(
    scope: AnyDescriptor | SubCommandType,
    values: dict[str, Any],
    errors: list[ValidationError],
    *,
    prefix: str,
) -> None:
    """Run cross-input checks on this scope, then recurse into sub-commands."""
    active = _active_input_ids(scope, values)
    errors.extend(_check_requires(scope, active, prefix))
    errors.extend(_check_disables(scope, active, prefix))
    errors.extend(_check_value_requires_disables(scope, values, active, prefix))

    for inp in scope.inputs or []:
        if inp.id not in values:
            continue
        child_value = values[inp.id]
        if isinstance(inp, SubCommandInput):
            _check_scope(
                inp.type,
                child_value,
                errors,
                prefix=f"{prefix}inputs[{inp.id}].type.",
            )
        elif isinstance(inp, SubCommandUnionInput):
            chosen_id = (
                child_value.get(DISCRIMINATOR_KEY) if isinstance(child_value, dict) else None
            )
            chosen = next((sc for sc in inp.type if sc.id == chosen_id), None)
            if chosen is not None:
                _check_scope(
                    chosen,
                    child_value,
                    errors,
                    prefix=f"{prefix}inputs[{inp.id}].type[{chosen_id}].",
                )


def _active_input_ids(
    scope: AnyDescriptor | SubCommandType,
    values: dict[str, Any],
) -> set[str]:
    """IDs of inputs the invocation activates within this scope.

    A ``Flag`` input is active only when its value is ``True``. Any
    other present-and-non-None input is active.
    """
    active: set[str] = set()
    for inp in scope.inputs or []:
        if inp.id not in values:
            continue
        value = values[inp.id]
        if isinstance(inp, FlagInput):
            if value is True:
                active.add(inp.id)
        elif value is not None:
            active.add(inp.id)
    return active


# ---------------------------------------------------------------------------
# Per-input checks
# ---------------------------------------------------------------------------


def _check_requires(
    scope: AnyDescriptor | SubCommandType,
    active: set[str],
    prefix: str,
) -> list[ValidationError]:
    """Each active input's ``requires-inputs`` IDs must also be active.

    A required ID may reference a group; that's satisfied by any active
    member of the group.
    """
    groups = getattr(scope, "groups", None) or []
    group_member_sets = {g.id: set(g.members) for g in groups}
    errors: list[ValidationError] = []
    for inp in scope.inputs or []:
        if inp.id not in active:
            continue
        for required in getattr(inp, "requires_inputs", None) or []:
            if required in active:
                continue
            members = group_member_sets.get(required)
            if members and (members & active):
                continue
            errors.append(
                ValidationError(
                    location=f"{prefix}inputs[{inp.id}].requires-inputs",
                    message=f"input {inp.id!r} requires {required!r} to be active.",
                )
            )
    return errors


def _check_disables(
    scope: AnyDescriptor | SubCommandType,
    active: set[str],
    prefix: str,
) -> list[ValidationError]:
    """An active input's ``disables-inputs`` IDs must NOT be active."""
    errors: list[ValidationError] = []
    for inp in scope.inputs or []:
        if inp.id not in active:
            continue
        for disabled in getattr(inp, "disables_inputs", None) or []:
            if disabled in active:
                errors.append(
                    ValidationError(
                        location=f"{prefix}inputs[{inp.id}].disables-inputs",
                        message=f"input {inp.id!r} disables {disabled!r}, which is active.",
                    )
                )
    return errors


def _check_value_requires_disables(
    scope: AnyDescriptor | SubCommandType,
    values: dict[str, Any],
    active: set[str],
    prefix: str,
) -> list[ValidationError]:
    """Per-choice requires/disables: only enforce for the active choice."""
    errors: list[ValidationError] = []
    for inp in scope.inputs or []:
        if inp.id not in active:
            continue
        chosen = str(values[inp.id])

        for choice, required_ids in (getattr(inp, "value_requires", None) or {}).items():
            if choice != chosen:
                continue
            for required in required_ids:
                if required not in active:
                    errors.append(
                        ValidationError(
                            location=f"{prefix}inputs[{inp.id}].value-requires",
                            message=(
                                f"value {choice!r} of {inp.id!r} requires "
                                f"{required!r} to be active."
                            ),
                        )
                    )

        for choice, disabled_ids in (getattr(inp, "value_disables", None) or {}).items():
            if choice != chosen:
                continue
            for disabled in disabled_ids:
                if disabled in active:
                    errors.append(
                        ValidationError(
                            location=f"{prefix}inputs[{inp.id}].value-disables",
                            message=(
                                f"value {choice!r} of {inp.id!r} disables "
                                f"{disabled!r}, which is active."
                            ),
                        )
                    )
    return errors


# ---------------------------------------------------------------------------
# Group checks (top-level only)
# ---------------------------------------------------------------------------


def _check_groups(
    descriptor: AnyDescriptor,
    values: dict[str, Any],
) -> list[ValidationError]:
    if not descriptor.groups:
        return []
    active = _active_input_ids(descriptor, values)
    errors: list[ValidationError] = []
    for group in descriptor.groups:
        members_active = [m for m in group.members if m in active]
        n_active = len(members_active)
        total = len(group.members)
        if group.mutually_exclusive and n_active > 1:
            errors.append(
                ValidationError(
                    location=f"groups[{group.id}]",
                    message=(
                        f"group {group.id!r} is mutually-exclusive; "
                        f"{n_active} members active: {sorted(members_active)}."
                    ),
                )
            )
        if group.one_is_required and n_active == 0:
            errors.append(
                ValidationError(
                    location=f"groups[{group.id}]",
                    message=f"group {group.id!r} requires at least one active member.",
                )
            )
        if group.all_or_none and 0 < n_active < total:
            errors.append(
                ValidationError(
                    location=f"groups[{group.id}]",
                    message=(
                        f"group {group.id!r} is all-or-none; "
                        f"{n_active}/{total} members active "
                        f"({sorted(members_active)})."
                    ),
                )
            )
    return errors


__all__ = [
    "InvocationValidationError",
    "validate_invocation",
]
