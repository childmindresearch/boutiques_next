"""`bosh exec` — simulate or launch a descriptor with an invocation."""

from __future__ import annotations

import json
import shlex
from pathlib import Path

import typer

from boutiques.execution import launch as _launch
from boutiques.execution import simulate as _simulate
from boutiques.execution.runtime.base import RuntimeError_
from boutiques.invocation_check import InvocationValidationError
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
    invocation: Path | None = typer.Argument(
        None,
        exists=True,
        readable=True,
        help="Invocation JSON file. May also be supplied via --invocation/-i.",
    ),
    invocation_flag: Path | None = typer.Option(
        None,
        "--invocation",
        "-i",
        exists=True,
        readable=True,
        help="Invocation JSON file (alternative to the positional argument; matches classic bosh).",
    ),
) -> None:
    """Resolve a descriptor + invocation into a command-line without running it."""
    try:
        parsed = load(descriptor)
    except DescriptorLoadError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    invocation_path = _pick_invocation(invocation, invocation_flag)
    if invocation_path is None:
        typer.echo(
            "Provide an invocation, either positionally or via --invocation/-i.",
            err=True,
        )
        raise typer.Exit(1)

    inv = json.loads(invocation_path.read_text())
    try:
        typer.echo(_simulate(parsed, inv))
    except InvocationValidationError as exc:
        typer.echo(f"Invocation invalid:\n{exc}", err=True)
        raise typer.Exit(1) from exc


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
    runtime_args: str = typer.Option(
        "",
        "--runtime-args",
        help=(
            "Extra arguments passed through to the container runtime, "
            "shlex-split. Example: --runtime-args '--gpus all --network host'."
        ),
    ),
    volumes: list[str] = typer.Option(
        [],
        "--volumes",
        "-v",
        help=(
            "Compat with classic bosh: HOST:CONTAINER bind mount. Repeatable. "
            "Each pair is appended to the container runtime's argv as '-v <pair>'."
        ),
    ),
    force_docker: bool = typer.Option(
        False, "--force-docker", help="Compat: equivalent to '-r docker'."
    ),
    force_singularity: bool = typer.Option(
        False,
        "--force-singularity",
        help="Compat: equivalent to '-r singularity'.",
    ),
    force_apptainer: bool = typer.Option(
        False,
        "--force-apptainer",
        help="Compat: equivalent to '-r singularity' (Apptainer is selected automatically).",
    ),
) -> None:
    """Launch a descriptor with an invocation under the chosen runtime."""
    try:
        parsed = load(descriptor)
    except DescriptorLoadError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    try:
        runtime = _resolve_runtime(runtime, force_docker, force_singularity, force_apptainer)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1) from exc

    extra_args = shlex.split(runtime_args) if runtime_args else []
    for vol in volumes:
        extra_args.extend(["-v", vol])

    inv = json.loads(invocation.read_text())
    try:
        result = _launch(
            parsed,
            inv,
            runtime=runtime,
            cwd=cwd,
            runtime_args=extra_args,
            stream=True,
            capture=False,  # output already streamed; don't buffer twice
        )
    except InvocationValidationError as exc:
        typer.echo(f"Invocation invalid:\n{exc}", err=True)
        raise typer.Exit(1) from exc
    except RuntimeError_ as exc:
        typer.echo(f"Runtime error: {exc}", err=True)
        raise typer.Exit(2) from exc

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


def _pick_invocation(
    positional: Path | None,
    via_flag: Path | None,
) -> Path | None:
    """Reconcile the positional and -i ways of passing an invocation."""
    if positional is not None and via_flag is not None:
        typer.echo(
            "Pass invocation positionally or via --invocation/-i, not both.",
            err=True,
        )
        raise typer.Exit(1)
    return positional if positional is not None else via_flag


def _resolve_runtime(
    runtime: str,
    force_docker: bool,
    force_singularity: bool,
    force_apptainer: bool,
) -> str:
    """Reconcile -r with classic bosh's --force-* compatibility flags."""
    force = [
        ("docker", force_docker),
        ("singularity", force_singularity or force_apptainer),
    ]
    selected = [name for name, active in force if active]
    if len(selected) > 1:
        raise ValueError(
            "Pass at most one of --force-docker, --force-singularity, --force-apptainer."
        )
    if selected:
        forced = selected[0]
        # If -r was also explicitly set to a non-default value that conflicts, error.
        if runtime != "local" and runtime != forced:
            raise ValueError(
                f"--force-* selects {forced!r} but -r is set to {runtime!r}; pick one."
            )
        return forced
    return runtime


def register(app: typer.Typer) -> None:
    app.add_typer(exec_app)
