"""Input helpers for the CLI."""

from __future__ import annotations

import typer

from boutiques.loader import (
    AnyDescriptor,
    DescriptorLoadError,
    load_descriptor,
    load_invocation,
)


def load_descriptor_or_exit(source: str) -> AnyDescriptor:
    """Load a descriptor or abort the CLI."""
    try:
        return load_descriptor(source)
    except DescriptorLoadError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc


def load_invocation_or_exit(source: str) -> dict[str, object]:
    """Load an invocation or abort the CLI."""
    try:
        return load_invocation(source)
    except (OSError, ValueError) as exc:
        typer.echo(f"Could not read invocation: {exc}", err=True)
        raise typer.Exit(1) from exc
