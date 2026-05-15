"""Tests for the ``bosh test`` runner."""

from __future__ import annotations

import hashlib
import json
import sys

from typer.testing import CliRunner

from boutiques.cli import app
from boutiques.loader import load
from boutiques.run_tests import run_tests

runner = CliRunner()


def _descriptor_with_tests(tmp_path, tests):
    """A descriptor that runs a tiny python snippet and (optionally) declares an output."""
    return load(
        {
            "schema-version": "0.5",
            "name": "tiny",
            "description": "trivial wrapper for testing",
            "tool-version": "1.0",
            "command-line": "[PYTHON] -c [SCRIPT]",
            "inputs": [
                {"id": "python", "name": "P", "type": "String", "value-key": "[PYTHON]"},
                {"id": "script", "name": "S", "type": "String", "value-key": "[SCRIPT]"},
                {"id": "name", "name": "N", "type": "String", "value-key": "[NAME]"},
            ],
            "output-files": [
                {"id": "out", "name": "Out", "path-template": "[NAME].txt"}
            ],
            "tests": tests,
        }
    )


def test_passing_exit_code_assertion(tmp_path):
    d = _descriptor_with_tests(
        tmp_path,
        [
            {
                "name": "exits_zero",
                "invocation": {
                    "python": sys.executable,
                    "script": "pass",
                    "name": "unused",
                },
                "assertions": {"exit-code": 0},
            }
        ],
    )
    results = run_tests(d, cwd=tmp_path)
    assert results.passed
    assert results.num_passed == 1
    assert results.cases[0].name == "exits_zero"


def test_failing_exit_code_assertion(tmp_path):
    d = _descriptor_with_tests(
        tmp_path,
        [
            {
                "name": "exits_seven",
                "invocation": {
                    "python": sys.executable,
                    "script": "import sys; sys.exit(7)",
                    "name": "unused",
                },
                "assertions": {"exit-code": 0},
            }
        ],
    )
    results = run_tests(d, cwd=tmp_path)
    assert not results.passed
    assert any("exit-code" in f for f in results.cases[0].failures)
    assert results.cases[0].exit_code == 7


def test_output_existence_passes(tmp_path):
    d = _descriptor_with_tests(
        tmp_path,
        [
            {
                "name": "creates_file",
                "invocation": {
                    "python": sys.executable,
                    "script": "open('result.txt', 'w').write('data')",
                    "name": "result",
                },
                "assertions": {"output-files": [{"id": "out"}]},
            }
        ],
    )
    results = run_tests(d, cwd=tmp_path)
    assert results.passed
    assert (tmp_path / "result.txt").exists()


def test_missing_output_fails(tmp_path):
    d = _descriptor_with_tests(
        tmp_path,
        [
            {
                "name": "no_file_produced",
                "invocation": {
                    "python": sys.executable,
                    "script": "pass",  # doesn't create result.txt
                    "name": "result",
                },
                "assertions": {"output-files": [{"id": "out"}]},
            }
        ],
    )
    results = run_tests(d, cwd=tmp_path)
    assert not results.passed
    assert any("missing" in f for f in results.cases[0].failures)


def test_md5_reference_match(tmp_path):
    content = b"deterministic content"
    expected_md5 = hashlib.md5(content).hexdigest()
    d = _descriptor_with_tests(
        tmp_path,
        [
            {
                "name": "matches_md5",
                "invocation": {
                    "python": sys.executable,
                    "script": (
                        "open('result.txt', 'wb').write(b'deterministic content')"
                    ),
                    "name": "result",
                },
                "assertions": {
                    "output-files": [{"id": "out", "md5-reference": expected_md5}]
                },
            }
        ],
    )
    results = run_tests(d, cwd=tmp_path)
    assert results.passed, results.cases[0].failures


def test_md5_mismatch_reports_diff(tmp_path):
    d = _descriptor_with_tests(
        tmp_path,
        [
            {
                "name": "wrong_md5",
                "invocation": {
                    "python": sys.executable,
                    "script": "open('result.txt', 'wb').write(b'actual content')",
                    "name": "result",
                },
                "assertions": {
                    "output-files": [{"id": "out", "md5-reference": "0" * 32}]
                },
            }
        ],
    )
    results = run_tests(d, cwd=tmp_path)
    assert not results.passed
    assert any("md5 mismatch" in f for f in results.cases[0].failures)


def test_descriptor_with_no_tests(tmp_path):
    d = load(
        {
            "schema-version": "0.5",
            "name": "no_tests",
            "description": "x",
            "tool-version": "1.0",
            "command-line": "[X]",
            "inputs": [{"id": "x", "name": "X", "type": "String", "value-key": "[X]"}],
        }
    )
    results = run_tests(d, cwd=tmp_path)
    assert results.cases == []
    assert results.passed  # vacuously true


def _write_descriptor(path, *, tests=None, command_line="[PYTHON] -c [SCRIPT]"):
    inputs = [
        {"id": "python", "name": "P", "type": "String", "value-key": "[PYTHON]"},
        {"id": "script", "name": "S", "type": "String", "value-key": "[SCRIPT]"},
    ]
    if "[X]" in command_line:
        inputs = [{"id": "x", "name": "X", "type": "String", "value-key": "[X]"}]
    descriptor = {
        "schema-version": "0.5",
        "name": "tiny",
        "description": "x",
        "tool-version": "1.0",
        "command-line": command_line,
        "inputs": inputs,
    }
    if tests is not None:
        descriptor["tests"] = tests
    path.write_text(json.dumps(descriptor))


def test_cli_reports_pass_and_exits_zero(tmp_path):
    descriptor_path = tmp_path / "descriptor.json"
    _write_descriptor(
        descriptor_path,
        tests=[
            {
                "name": "ok",
                "invocation": {"python": sys.executable, "script": "pass"},
                "assertions": {"exit-code": 0},
            }
        ],
    )
    result = runner.invoke(app, ["test", str(descriptor_path), "--cwd", str(tmp_path)])
    assert result.exit_code == 0
    assert "[PASS] ok" in result.stdout
    assert "1/1 passed" in result.stdout


def test_cli_reports_failure_and_exits_one(tmp_path):
    descriptor_path = tmp_path / "descriptor.json"
    _write_descriptor(
        descriptor_path,
        tests=[
            {
                "name": "bad",
                "invocation": {
                    "python": sys.executable,
                    "script": "import sys; sys.exit(2)",
                },
                "assertions": {"exit-code": 0},
            }
        ],
    )
    result = runner.invoke(app, ["test", str(descriptor_path), "--cwd", str(tmp_path)])
    assert result.exit_code == 1
    assert "[FAIL] bad" in result.stdout
    assert "0 passed, 1 failed" in result.stdout


def test_missing_binary_surfaces_as_test_failure(tmp_path):
    """A test case whose command isn't installed fails just that case, not the run."""
    d = load(
        {
            "schema-version": "0.5",
            "name": "t",
            "description": "x",
            "tool-version": "1.0",
            "command-line": "definitely_not_a_real_binary_42 [X]",
            "inputs": [{"id": "x", "name": "X", "type": "String", "value-key": "[X]"}],
            "tests": [
                {
                    "name": "wont_run",
                    "invocation": {"x": "v"},
                    "assertions": {"exit-code": 0},
                }
            ],
        }
    )
    results = run_tests(d, cwd=tmp_path)
    assert not results.passed
    assert any("Command not found" in f for f in results.cases[0].failures)


def test_cli_no_tests_reports_and_exits_zero(tmp_path):
    descriptor_path = tmp_path / "descriptor.json"
    _write_descriptor(descriptor_path, command_line="[X]")
    result = runner.invoke(app, ["test", str(descriptor_path)])
    assert result.exit_code == 0
    assert "no tests declared" in result.stdout
