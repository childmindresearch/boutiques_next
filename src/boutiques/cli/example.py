"""`bosh example` — generate a sample invocation for a descriptor."""

from __future__ import annotations

import json

import typer

from boutiques.cli._input import load_descriptor_or_exit
from boutiques.example import generate


def register(app: typer.Typer) -> None:
    @app.command("example")
    def example(
        descriptor: str = typer.Argument(
            ..., help="Path or http(s) URL to a Boutiques descriptor."
        ),
        complete: bool = typer.Option(
            False,
            "--complete",
            "-c",
            help="Fill in optional inputs as well as required ones.",
        ),
    ) -> None:
        """Generate a sample invocation for a descriptor."""
        parsed = load_descriptor_or_exit(descriptor)
        invocation = generate(parsed, complete=complete)
        typer.echo(json.dumps(invocation, indent=2))
