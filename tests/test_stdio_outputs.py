"""Tests for v0.5+styx ``stdout-output`` / ``stderr-output`` fields."""

from __future__ import annotations

import sys

import pytest

from boutiques.execution import launch
from boutiques.execution.outputs import resolve_stdio_outputs
from boutiques.loader import DescriptorLoadError, load
from boutiques.models.v05_styx import StderrOutput, StdoutOutput


def _make(extra=None):
    base = {
        "schema-version": "0.5+styx",
        "name": "t",
        "description": "x",
        "tool-version": "1.0",
        "command-line": "tool [X]",
        "inputs": [{"id": "x", "name": "X", "type": "String", "value-key": "[X]"}],
    }
    if extra:
        base.update(extra)
    return load(base)


# ---- Model loading -------------------------------------------------------


def test_stdout_output_loads_under_v05_styx():
    d = _make({"stdout-output": {"id": "results", "name": "Tool output"}})
    assert isinstance(d.stdout_output, StdoutOutput)
    assert d.stdout_output.id == "results"
    assert d.stdout_output.name == "Tool output"


def test_stderr_output_loads_under_v05_styx():
    d = _make({"stderr-output": {"id": "log"}})
    assert isinstance(d.stderr_output, StderrOutput)
    assert d.stderr_output.id == "log"


def test_both_stdio_outputs_coexist():
    d = _make(
        {
            "stdout-output": {"id": "data"},
            "stderr-output": {"id": "log"},
        }
    )
    assert d.stdout_output and d.stdout_output.id == "data"
    assert d.stderr_output and d.stderr_output.id == "log"


def test_v05_rejects_stdout_output():
    """v0.5 stays strict — only v0.5+styx accepts these fields."""
    with pytest.raises(DescriptorLoadError, match="Extra inputs are not permitted"):
        load(
            {
                "schema-version": "0.5",
                "name": "t",
                "description": "x",
                "tool-version": "1.0",
                "command-line": "tool [X]",
                "inputs": [{"id": "x", "name": "X", "type": "String", "value-key": "[X]"}],
                "stdout-output": {"id": "out"},
            }
        )


# ---- Output resolution helper -------------------------------------------


def test_resolve_stdio_outputs_returns_captured_content():
    d = _make(
        {
            "stdout-output": {"id": "out", "name": "Output"},
            "stderr-output": {"id": "err"},
        }
    )
    outputs = resolve_stdio_outputs(d, stdout="hello\n", stderr="warning: x\n")
    by_id = {o.id: o for o in outputs}
    assert by_id["out"].content == "hello\n"
    assert by_id["out"].path is None
    assert by_id["out"].name == "Output"
    assert by_id["err"].content == "warning: x\n"
    assert by_id["err"].name == "err"  # fell back to id since no name declared


def test_resolve_stdio_outputs_returns_empty_when_not_declared():
    d = _make()  # no stdio outputs
    assert resolve_stdio_outputs(d, "anything", "anything") == []


# ---- Integration with launch -------------------------------------------


def test_launch_surfaces_stdio_outputs_with_content(tmp_path):
    """End-to-end: declare stdout-output, run a tool, get content via outputs list."""
    d = _make(
        {
            "command-line": "[PYTHON] -c [SCRIPT]",
            "inputs": [
                {"id": "python", "name": "P", "type": "String", "value-key": "[PYTHON]"},
                {"id": "script", "name": "S", "type": "String", "value-key": "[SCRIPT]"},
            ],
            "stdout-output": {"id": "result", "name": "Result"},
        }
    )
    result = launch(
        d,
        {
            "python": sys.executable,
            "script": "print('captured')",
        },
        runtime="local",
        cwd=tmp_path,
        stream=False,
    )
    by_id = {o.id: o for o in result.outputs}
    assert "result" in by_id
    assert "captured" in by_id["result"].content
    assert by_id["result"].path is None


def test_launch_omits_stdio_outputs_when_not_declared(tmp_path):
    """Outputs list contains only file outputs when no stdio outputs are declared."""
    d = _make(
        {
            "command-line": "[PYTHON] -c [SCRIPT]",
            "inputs": [
                {"id": "python", "name": "P", "type": "String", "value-key": "[PYTHON]"},
                {"id": "script", "name": "S", "type": "String", "value-key": "[SCRIPT]"},
            ],
        }
    )
    result = launch(
        d,
        {"python": sys.executable, "script": "print('hi')"},
        runtime="local",
        cwd=tmp_path,
        stream=False,
    )
    # stdout/stderr are captured on LaunchResult itself, but no ResolvedOutput
    # for them since they weren't declared.
    assert result.outputs == []
    assert "hi" in result.stdout
