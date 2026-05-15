"""`bosh example` — generate a sample invocation for a descriptor."""

from __future__ import annotations

from pathlib import Path

import typer


def register(app: typer.Typer) -> None:
    @app.command("example")
    def example(
        descriptor: Path = typer.Argument(..., exists=True, readable=True),
        complete: bool = typer.Option(
            False,
            "--complete",
            help="Fill in optional inputs as well as required ones.",
        ),
    ) -> None:
        """Generate a sample invocation for a descriptor."""
        raise NotImplementedError
