"""Apptainer runtime: wrap the argv in an ``apptainer exec`` invocation."""

from __future__ import annotations

from boutiques.execution.runtime._singularity_style import make_run

run = make_run("apptainer")
