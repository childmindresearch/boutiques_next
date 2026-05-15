"""`bosh exec` — simulate or launch a descriptor with an invocation."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from boutiques.execution import simulate as _simulate
from boutiques.loader import DescriptorLoadError, load

exec_app = typer.Typer(
    name="exec",
    help="Simulate or launch a descriptor.",
    no_args_is_help=True,
)


@exec_app.command("simulate")
def simulate(
    descriptor: str = typer.Argument(
        ..., help="Path or http(s) URL to a Boutiques descriptor."
    ),
    invocation: Path = typer.Argument(..., exists=True, readable=True),
) -> None:
    """Resolve a descriptor + invocation into a command-line without running it."""
    try:
        parsed = load(descriptor)
    except DescriptorLoadError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    inv = json.loads(invocation.read_text())
    typer.echo(_simulate(parsed, inv))


@exec_app.command("launch")
def launch(
    descriptor: str = typer.Argument(
        ..., help="Path or http(s) URL to a Boutiques descriptor."
    ),
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
