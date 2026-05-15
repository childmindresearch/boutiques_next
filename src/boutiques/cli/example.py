"""`bosh example` — generate a sample invocation for a descriptor."""

from __future__ import annotations

import json

import typer

from boutiques.example import generate
from boutiques.loader import DescriptorLoadError, load


def register(app: typer.Typer) -> None:
    @app.command("example")
    def example(
        descriptor: str = typer.Argument(
            ..., help="Path or http(s) URL to a Boutiques descriptor."
        ),
        complete: bool = typer.Option(
            False,
            "--complete",
            help="Fill in optional inputs as well as required ones.",
        ),
    ) -> None:
        """Generate a sample invocation for a descriptor."""
        try:
            parsed = load(descriptor)
        except DescriptorLoadError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc
        invocation = generate(parsed, complete=complete)
        typer.echo(json.dumps(invocation, indent=2))
