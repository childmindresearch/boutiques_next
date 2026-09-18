"""`bosh pprint` — render a descriptor as a structured tree view."""

from __future__ import annotations

import typer
from rich.console import Console

from boutiques.cli._input import load_descriptor_or_exit
from boutiques.prettyprint import pprint as _pprint


def register(app: typer.Typer) -> None:
    @app.command("pprint")
    def pprint(
        descriptor: str = typer.Argument(
            ..., help="Path or http(s) URL to a Boutiques descriptor."
        ),
        no_color: bool = typer.Option(
            False,
            "--no-color",
            help="Force ANSI colour off (useful when piping to a file).",
        ),
    ) -> None:
        """Pretty-print a Boutiques descriptor."""
        parsed = load_descriptor_or_exit(descriptor)

        console = Console(no_color=no_color)
        _pprint(parsed, console=console)
