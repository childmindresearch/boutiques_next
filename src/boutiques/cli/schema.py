"""`bosh schema-export` — emit the JSON Schema for one or both versions."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from boutiques.schema_export import VERSIONS, export_all, schema_for


def register(app: typer.Typer) -> None:
    @app.command("schema-export")
    def schema_export(
        output: Path = typer.Option(
            Path("docs/schema"),
            "--output",
            "-o",
            help="Directory to write descriptor.schema.json files into.",
        ),
        version: str = typer.Option(
            "",
            "--version",
            help=f"Limit output to a single version. Known: {', '.join(sorted(VERSIONS))}.",
        ),
        stdout: bool = typer.Option(
            False,
            "--stdout",
            help="Print the schema to stdout instead of writing to disk. Requires --version.",
        ),
    ) -> None:
        """Generate JSON Schema artifacts from the Pydantic models."""
        if version and version not in VERSIONS:
            known = ", ".join(sorted(VERSIONS))
            typer.echo(
                f"Unknown schema version {version!r}. Known: {known}.",
                err=True,
            )
            raise typer.Exit(1)

        if stdout:
            if not version:
                typer.echo(
                    "--stdout requires --version (cannot print multiple schemas at once).",
                    err=True,
                )
                raise typer.Exit(1)
            typer.echo(json.dumps(schema_for(version), indent=2))
            return

        if version:
            target_dir = output / version
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / "descriptor.schema.json"
            target.write_text(json.dumps(schema_for(version), indent=2) + "\n")
            typer.echo(f"Wrote {target}")
            return

        written = export_all(output)
        for path in written:
            typer.echo(f"Wrote {path}")
