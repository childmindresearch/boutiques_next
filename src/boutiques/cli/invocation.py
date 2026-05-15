"""`bosh invocation` — emit the invocation JSON Schema for a descriptor."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from boutiques.invocation import invocation_schema
from boutiques.loader import DescriptorLoadError, load


def register(app: typer.Typer) -> None:
    @app.command("invocation")
    def invocation(
        descriptor: str = typer.Argument(
            ..., help="Path or http(s) URL to a Boutiques descriptor."
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="File to write the invocation schema into. Without -o, prints to stdout.",
        ),
    ) -> None:
        """Emit the JSON Schema describing valid invocations for a descriptor.

        The schema is derived from the descriptor's inputs and reflects
        everything ``bosh exec simulate`` / ``launch`` will enforce
        structurally — required fields, types, value-choices,
        numeric ranges, list bounds, and sub-command unions.
        """
        try:
            parsed = load(descriptor)
        except DescriptorLoadError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc

        schema = invocation_schema(parsed)
        rendered = json.dumps(schema, indent=2)

        if output is None:
            typer.echo(rendered)
            return

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n")
        typer.echo(f"Wrote {output}", err=True)
