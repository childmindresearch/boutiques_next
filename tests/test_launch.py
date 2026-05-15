"""Launch tests: local end-to-end + docker/singularity argv assertions."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from boutiques.execution import launch
from boutiques.execution.runtime.base import RunResult, RuntimeError_
from boutiques.loader import load


def _echo_descriptor():
    """A trivial descriptor that wraps the platform 'echo'-like behavior."""
    return load(
        {
            "schema-version": "0.5",
            "name": "echo_test",
            "description": "Print a message and exit",
            "tool-version": "1.0",
            "command-line": "[PYTHON] -c [SCRIPT] [MSG]",
            "inputs": [
                {
                    "id": "python",
                    "name": "Python",
                    "type": "String",
                    "value-key": "[PYTHON]",
                },
                {
                    "id": "script",
                    "name": "Script",
                    "type": "String",
                    "value-key": "[SCRIPT]",
                },
                {
                    "id": "msg",
                    "name": "Message",
                    "type": "String",
                    "value-key": "[MSG]",
                },
            ],
        }
    )


def test_local_runtime_runs_real_subprocess(tmp_path):
    """End-to-end: invoke real Python via the local runtime."""
    descriptor = _echo_descriptor()
    result = launch(
        descriptor,
        {
            "python": sys.executable,
            "script": "import sys; print('hi from', sys.argv[1])",
            "msg": "boutiques",
        },
        runtime="local",
        cwd=tmp_path,
    )
    assert result.exit_code == 0
    assert "hi from boutiques" in result.stdout
    assert result.runtime == "local"
    assert result.command[0] == sys.executable


def test_local_runtime_propagates_exit_code(tmp_path):
    descriptor = _echo_descriptor()
    result = launch(
        descriptor,
        {
            "python": sys.executable,
            "script": "import sys; sys.exit(7)",
            "msg": "",
        },
        runtime="local",
        cwd=tmp_path,
    )
    assert result.exit_code == 7


def _docker_descriptor():
    return load(
        {
            "schema-version": "0.5",
            "name": "in_container",
            "description": "Runs in a container",
            "tool-version": "1.0",
            "command-line": "do_thing [X]",
            "inputs": [
                {"id": "x", "name": "X", "type": "String", "value-key": "[X]"},
            ],
            "container-image": {"type": "docker", "image": "example/tool"},
        }
    )


def test_docker_runtime_wraps_argv(tmp_path):
    descriptor = _docker_descriptor()

    captured = {}

    def fake_run(argv, capture_output, text, check):
        captured["argv"] = argv

        class _Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return _Result()

    with patch("boutiques.execution.runtime.docker.subprocess.run", side_effect=fake_run):
        launch(descriptor, {"x": "hello"}, runtime="docker", cwd=tmp_path)

    argv = captured["argv"]
    assert argv[:3] == ["docker", "run", "--rm"]
    assert "-v" in argv and "-w" in argv
    assert "example/tool" in argv
    # Tool argv appears after the image reference
    image_idx = argv.index("example/tool")
    assert argv[image_idx + 1 :] == ["do_thing", "hello"]


def test_docker_with_index_prepends_registry(tmp_path):
    descriptor = load(
        {
            "schema-version": "0.5",
            "name": "x",
            "description": "y",
            "tool-version": "1.0",
            "command-line": "tool",
            "inputs": [
                {"id": "a", "name": "A", "type": "String", "value-key": "[A]"},
            ],
            "container-image": {
                "type": "docker",
                "image": "bids/mriqc",
                "index": "docker.io",
            },
        }
    )

    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv

        class _Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return _Result()

    with patch("boutiques.execution.runtime.docker.subprocess.run", side_effect=fake_run):
        # The 'a' input is unused; CLI template has no [A] so simulator drops it
        launch(descriptor, {"a": "val"}, runtime="docker", cwd=Path.cwd())

    assert "docker.io/bids/mriqc" in captured["argv"]


def test_docker_requires_container_image(tmp_path):
    descriptor = _echo_descriptor()  # no container-image
    with pytest.raises(RuntimeError_, match="docker runtime requires"):
        launch(descriptor, {"python": "p", "script": "s", "msg": "m"}, runtime="docker", cwd=tmp_path)


def test_singularity_runtime_uses_docker_uri(tmp_path):
    descriptor = _docker_descriptor()

    captured = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv

        class _Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return _Result()

    with patch(
        "boutiques.execution.runtime.singularity.subprocess.run", side_effect=fake_run
    ), patch("boutiques.execution.runtime.singularity.shutil.which", return_value=None):
        launch(descriptor, {"x": "hi"}, runtime="singularity", cwd=tmp_path)

    argv = captured["argv"]
    assert argv[0] == "singularity"
    assert "exec" in argv
    assert "--bind" in argv and "--pwd" in argv
    assert "docker://example/tool" in argv


def test_unknown_runtime_raises():
    descriptor = _echo_descriptor()
    with pytest.raises(RuntimeError_, match="Unknown runtime"):
        launch(descriptor, {"python": "p", "script": "s", "msg": "m"}, runtime="podman")


def test_output_paths_resolve_against_cwd(tmp_path):
    """Path-template substitution + existence check. Skips the subprocess."""
    descriptor = load(
        {
            "schema-version": "0.5",
            "name": "with_output",
            "description": "x",
            "tool-version": "1.0",
            "command-line": "true [NAME]",
            "inputs": [
                {"id": "name", "name": "N", "type": "String", "value-key": "[NAME]"},
            ],
            "output-files": [
                {
                    "id": "out",
                    "name": "Out",
                    "path-template": "[NAME].txt",
                }
            ],
        }
    )
    # Create the expected output so the existence check is true
    (tmp_path / "result.txt").write_text("data")

    # Bypass the subprocess to keep this test platform-agnostic.
    from boutiques.execution.outputs import resolve_output_paths

    outputs = resolve_output_paths(descriptor, {"name": "result"}, tmp_path)
    assert len(outputs) == 1
    out = outputs[0]
    assert out.id == "out"
    assert out.path == (tmp_path / "result.txt").resolve()
    assert out.exists


def test_environment_variables_are_passed(tmp_path):
    """Env vars declared by the descriptor reach the subprocess."""
    descriptor = load(
        {
            "schema-version": "0.5",
            "name": "env_check",
            "description": "x",
            "tool-version": "1.0",
            "command-line": "[PYTHON] -c [SCRIPT]",
            "inputs": [
                {"id": "python", "name": "P", "type": "String", "value-key": "[PYTHON]"},
                {"id": "script", "name": "S", "type": "String", "value-key": "[SCRIPT]"},
            ],
            "environment-variables": [
                {"name": "BOUTIQUES_TEST_VAR", "value": "from_descriptor"}
            ],
        }
    )
    result = launch(
        descriptor,
        {
            "python": sys.executable,
            "script": "import os; print(os.environ['BOUTIQUES_TEST_VAR'])",
        },
        runtime="local",
        cwd=tmp_path,
    )
    assert result.exit_code == 0
    assert "from_descriptor" in result.stdout
