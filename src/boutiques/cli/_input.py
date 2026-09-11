"""Shared CLI input helpers."""

from __future__ import annotations

import typer

from boutiques.loader import read_data


def read_invocation(source: str) -> dict[str, object]:
    """Read an invocation from a JSON file path or a JSON string, or abort."""
    try:
        return read_data(source)
    except (OSError, ValueError) as exc:
        typer.echo(f"Could not read invocation: {exc}", err=True)
        raise typer.Exit(1) from exc
