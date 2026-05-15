"""`bosh exec` — simulate or launch a descriptor with an invocation."""

from __future__ import annotations

import json
from pathlib import Path

import typer

from boutiques.execution import launch as _launch
from boutiques.execution import simulate as _simulate
from boutiques.execution.runtime.base import RuntimeError_
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
    cwd: Path = typer.Option(
        Path.cwd(),
        "--cwd",
        help="Working directory for the run (also the container mount point).",
    ),
) -> None:
    """Launch a descriptor with an invocation under the chosen runtime."""
    try:
        parsed = load(descriptor)
    except DescriptorLoadError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc
    inv = json.loads(invocation.read_text())
    try:
        result = _launch(parsed, inv, runtime=runtime, cwd=cwd)
    except RuntimeError_ as exc:
        typer.echo(f"Runtime error: {exc}", err=True)
        raise typer.Exit(2) from exc

    if result.stdout:
        typer.echo(result.stdout, nl=False)
    if result.stderr:
        typer.echo(result.stderr, err=True, nl=False)
    typer.echo(
        f"\n[bosh] runtime={result.runtime} "
        f"exit={result.exit_code} "
        f"duration={result.duration_seconds:.2f}s",
        err=True,
    )
    if result.outputs:
        typer.echo("[bosh] declared outputs:", err=True)
        for o in result.outputs:
            marker = "OK" if o.exists else "missing"
            typer.echo(f"  [{marker}] {o.id}: {o.path}", err=True)
    raise typer.Exit(result.exit_code)


def register(app: typer.Typer) -> None:
    app.add_typer(exec_app)
