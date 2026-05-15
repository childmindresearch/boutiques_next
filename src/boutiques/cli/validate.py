"""`bosh validate` — check a descriptor against its schema."""

from __future__ import annotations

from pathlib import Path

import typer

from boutiques.validate import validate as _validate


def register(app: typer.Typer) -> None:
    @app.command("validate")
    def validate(
        descriptor: Path = typer.Argument(..., exists=True, readable=True),
    ) -> None:
        """Validate a Boutiques descriptor."""
        result = _validate(descriptor)
        if not result.ok:
            typer.echo(result.format(), err=True)
            raise typer.Exit(1)

        assert result.descriptor is not None
        version = result.descriptor.tool_version or "?"
        typer.echo(
            f"OK: {result.descriptor.name} "
            f"v{version} "
            f"({result.descriptor.schema_version})"
        )
        for warning in result.warnings:
            typer.echo(str(warning), err=True)
