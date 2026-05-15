"""`bosh version` — print the installed version."""

from __future__ import annotations

import typer

from boutiques import __version__


def register(app: typer.Typer) -> None:
    @app.command("version")
    def version() -> None:
        """Print the boutiques version."""
        typer.echo(__version__)
