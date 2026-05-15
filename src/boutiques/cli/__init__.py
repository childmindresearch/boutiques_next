"""bosh command-line interface.

Each subcommand lives in its own module and exposes a ``register(app)``
callable that attaches its commands to the shared Typer app. The CLI is
deliberately thin: each command parses arguments and delegates to a
function in the corresponding library module (``boutiques.validate``,
``boutiques.example``, ``boutiques.execution``, ...).
"""

from __future__ import annotations

import typer

from . import example, execute, validate, version

app = typer.Typer(
    name="bosh",
    help="Boutiques descriptor toolkit.",
    no_args_is_help=True,
    add_completion=False,
)

for module in (validate, example, execute, version):
    module.register(app)


__all__ = ["app"]
