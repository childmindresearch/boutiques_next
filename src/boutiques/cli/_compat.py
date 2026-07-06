"""Classic-``bosh`` compatibility surface for the ``exec`` CLI.

``boutiques_next`` aims to be a drop-in replacement for classic ``bosh``. To
keep existing tools (Nipoppy and friends) from breaking on "unrecognized
arguments", the ``exec`` commands accept the *full* classic flag set. Options
whose behavior is not wired up yet are accepted by the parser but refuse
loudly here — with a pointer to open an issue — rather than being silently
ignored, which could produce a run that quietly differs from classic ``bosh``.
"""

from __future__ import annotations

import typer

#: Where users should report reliance on a not-yet-implemented classic option.
ISSUE_URL = "https://github.com/childmindresearch/boutiques_next/issues"


def not_implemented(option: str) -> None:
    """Abort with a clear "classic option not implemented yet" message.

    Called from an ``exec`` command when the user actually passes a classic
    ``bosh`` option this runtime does not honor yet. We exit non-zero rather
    than ignore the option, so behavior never silently diverges from classic.
    """
    typer.echo(
        f"{option} is a classic-bosh option that is not implemented in this "
        f"runtime yet.\nIf you rely on it, please open an issue at {ISSUE_URL} "
        "so we can prioritize it.",
        err=True,
    )
    raise typer.Exit(2)
