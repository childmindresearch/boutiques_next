"""`bosh validate` — check a descriptor against its schema."""

from __future__ import annotations

from pathlib import Path

import typer


def register(app: typer.Typer) -> None:
    @app.command("validate")
    def validate(
        descriptor: Path = typer.Argument(..., exists=True, readable=True),
    ) -> None:
        """Validate a Boutiques descriptor."""
        raise NotImplementedError
