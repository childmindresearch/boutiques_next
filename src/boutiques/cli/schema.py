"""`bosh schema-export` — emit the JSON Schema for one or both versions."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from boutiques.schema_export import VERSIONS, export_all, schema_for

_DEFAULT_VERSION = "0.5+styx"


def register(app: typer.Typer) -> None:
    @app.command("schema-export")
    def schema_export(
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help=(
                "Directory to write descriptor.schema.json files into. "
                "If omitted, the schema is printed to stdout."
            ),
        ),
        version: str = typer.Option(
            "",
            "--version",
            help=(
                f"Limit output to a single version. Known: "
                f"{', '.join(sorted(VERSIONS))}. Defaults to {_DEFAULT_VERSION} "
                "when printing to stdout."
            ),
        ),
    ) -> None:
        """Generate JSON Schema artifacts from the Pydantic models.

        Without ``-o``, the schema is printed to stdout (one version per
        invocation). With ``-o``, the file is written to disk; if
        ``--version`` is omitted, every known version is written.
        """
        if version and version not in VERSIONS:
            known = ", ".join(sorted(VERSIONS))
            typer.echo(f"Unknown schema version {version!r}. Known: {known}.", err=True)
            raise typer.Exit(1)

        # No --output → print to stdout (one version).
        if output is None:
            chosen = version or _DEFAULT_VERSION
            typer.echo(json.dumps(schema_for(chosen), indent=2))
            return

        # --output set → write to disk.
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
