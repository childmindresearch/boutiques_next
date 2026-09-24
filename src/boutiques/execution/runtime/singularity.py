"""Singularity runtime: wrap the argv in a ``singularity exec`` invocation."""

from __future__ import annotations

from boutiques.execution.runtime._singularity_style import make_run

run = make_run("singularity")
