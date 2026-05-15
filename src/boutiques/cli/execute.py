"""`bosh exec` — simulate or launch a descriptor with an invocation."""

from __future__ import annotations

from pathlib import Path

import typer

exec_app = typer.Typer(
    name="exec",
    help="Simulate or launch a descriptor.",
    no_args_is_help=True,
)


@exec_app.command("simulate")
def simulate(
    descriptor: Path = typer.Argument(..., exists=True, readable=True),
    invocation: Path = typer.Argument(..., exists=True, readable=True),
) -> None:
    """Resolve a descriptor + invocation into a command-line without running it."""
    raise NotImplementedError


@exec_app.command("launch")
def launch(
    descriptor: Path = typer.Argument(..., exists=True, readable=True),
    invocation: Path = typer.Argument(..., exists=True, readable=True),
    runtime: str = typer.Option(
        "local",
        "--runtime",
        "-r",
        help="Runtime backend: local, docker, singularity.",
    ),
) -> None:
    """Launch a descriptor with an invocation under the chosen runtime."""
    raise NotImplementedError


def register(app: typer.Typer) -> None:
    app.add_typer(exec_app)
