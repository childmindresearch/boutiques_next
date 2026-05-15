"""`bosh test` — run the test cases embedded in a descriptor."""

from __future__ import annotations

from pathlib import Path

import typer

from boutiques.execution.runtime.base import RuntimeError_
from boutiques.loader import DescriptorLoadError, load
from boutiques.run_tests import run_tests as _run_tests


def register(app: typer.Typer) -> None:
    @app.command("test")
    def test(
        descriptor: str = typer.Argument(
            ..., help="Path or http(s) URL to a Boutiques descriptor."
        ),
        runtime: str = typer.Option(
            "local",
            "--runtime",
            "-r",
            help="Runtime backend: local, docker, singularity.",
        ),
        cwd: Path = typer.Option(
            Path.cwd(),
            "--cwd",
            help="Working directory for the runs (also the container mount point).",
        ),
    ) -> None:
        """Run every test case declared on the descriptor."""
        try:
            parsed = load(descriptor)
        except DescriptorLoadError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc

        if not parsed.tests:
            typer.echo(f"{parsed.name}: no tests declared.")
            return

        try:
            results = _run_tests(parsed, runtime=runtime, cwd=cwd)
        except RuntimeError_ as exc:
            typer.echo(f"Runtime error: {exc}", err=True)
            raise typer.Exit(2) from exc

        for case in results.cases:
            marker = "PASS" if case.passed else "FAIL"
            typer.echo(f"[{marker}] {case.name} ({case.duration_seconds:.2f}s)")
            for failure in case.failures:
                typer.echo(f"        {failure}")

        total = len(results.cases)
        summary = (
            f"{results.num_passed}/{total} passed"
            if results.passed
            else f"{results.num_passed} passed, {results.num_failed} failed (of {total})"
        )
        typer.echo(f"\n[bosh test] {results.descriptor_name}: {summary}")
        raise typer.Exit(0 if results.passed else 1)
