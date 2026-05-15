"""Launch tests: local end-to-end + docker/singularity argv assertions."""

from __future__ import annotations

import sys
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
                {"id": "python", "name": "P", "type": "String", "value-key": "[PYTHON]"},
                {"id": "script", "name": "S", "type": "String", "value-key": "[SCRIPT]"},
                {"id": "msg", "name": "M", "type": "String", "value-key": "[MSG]"},
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
        stream=False,
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
        stream=False,
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


def _fake_run_subprocess(captured: dict):
    """A run_subprocess stand-in that records its argv and returns success."""

    def _impl(argv, **kwargs):
        captured["argv"] = argv
        captured["kwargs"] = kwargs
        return RunResult(exit_code=0, stdout="", stderr="", duration_seconds=0.0)

    return _impl


def test_docker_runtime_wraps_argv(tmp_path):
    captured: dict = {}
    with patch(
        "boutiques.execution.runtime.docker.run_subprocess",
        side_effect=_fake_run_subprocess(captured),
    ):
        launch(_docker_descriptor(), {"x": "hello"}, runtime="docker", cwd=tmp_path)

    argv = captured["argv"]
    assert argv[:3] == ["docker", "run", "--rm"]
    assert "-v" in argv and "-w" in argv
    assert "example/tool" in argv
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
    captured: dict = {}
    with patch(
        "boutiques.execution.runtime.docker.run_subprocess",
        side_effect=_fake_run_subprocess(captured),
    ):
        launch(descriptor, {"a": "val"}, runtime="docker", cwd=tmp_path)

    assert "docker.io/bids/mriqc" in captured["argv"]


def test_docker_requires_container_image(tmp_path):
    descriptor = _echo_descriptor()  # no container-image
    with pytest.raises(RuntimeError_, match="docker runtime requires"):
        launch(
            descriptor,
            {"python": "p", "script": "s", "msg": "m"},
            runtime="docker",
            cwd=tmp_path,
        )


def test_runtime_args_pass_through_to_docker(tmp_path):
    """--runtime-args content is inserted before the image ref, after our flags."""
    captured: dict = {}
    with patch(
        "boutiques.execution.runtime.docker.run_subprocess",
        side_effect=_fake_run_subprocess(captured),
    ):
        launch(
            _docker_descriptor(),
            {"x": "hi"},
            runtime="docker",
            cwd=tmp_path,
            runtime_args=["--gpus", "all", "--network", "host"],
        )

    argv = captured["argv"]
    # All four runtime-arg tokens appear and are before the image ref.
    image_idx = argv.index("example/tool")
    for token in ("--gpus", "all", "--network", "host"):
        idx = argv.index(token)
        assert idx < image_idx, f"{token!r} should precede image ref"


def test_singularity_runtime_uses_docker_uri(tmp_path):
    captured: dict = {}
    with (
        patch(
            "boutiques.execution.runtime.singularity.run_subprocess",
            side_effect=_fake_run_subprocess(captured),
        ),
        patch(
            "boutiques.execution.runtime.singularity.shutil.which",
            return_value=None,
        ),
    ):
        launch(_docker_descriptor(), {"x": "hi"}, runtime="singularity", cwd=tmp_path)

    argv = captured["argv"]
    assert argv[0] == "singularity"
    assert "exec" in argv
    assert "--bind" in argv and "--pwd" in argv
    assert "docker://example/tool" in argv


def test_cli_force_docker_aliases_runtime(tmp_path):
    """`--force-docker` (classic-bosh compat) selects the docker runtime, -v appends mounts."""
    import json

    from typer.testing import CliRunner

    from boutiques.cli import app

    descriptor_path = tmp_path / "descriptor.json"
    descriptor_path.write_text(
        json.dumps(
            {
                "schema-version": "0.5",
                "name": "t",
                "description": "x",
                "tool-version": "1.0",
                "command-line": "tool [X]",
                "inputs": [
                    {"id": "x", "name": "X", "type": "String", "value-key": "[X]"}
                ],
                "container-image": {"type": "docker", "image": "example/tool"},
            }
        )
    )
    inv_path = tmp_path / "inv.json"
    inv_path.write_text('{"x": "v"}')

    captured: dict = {}

    def fake_run(argv, **kwargs):
        captured["argv"] = argv
        return RunResult(exit_code=0, stdout="", stderr="", duration_seconds=0.0)

    with patch(
        "boutiques.execution.runtime.docker.run_subprocess", side_effect=fake_run
    ):
        result = CliRunner().invoke(
            app,
            [
                "exec",
                "launch",
                str(descriptor_path),
                str(inv_path),
                "--force-docker",
                "-v",
                "/a:/b",
                "-v",
                "/c:/d",
            ],
        )

    assert result.exit_code == 0
    argv = captured["argv"]
    assert argv[0] == "docker"
    for pair in ("/a:/b", "/c:/d"):
        assert pair in argv


def test_cli_force_multiple_runtimes_errors(tmp_path):
    import json

    from typer.testing import CliRunner

    from boutiques.cli import app

    descriptor_path = tmp_path / "descriptor.json"
    descriptor_path.write_text(
        json.dumps(
            {
                "schema-version": "0.5",
                "name": "t",
                "description": "x",
                "tool-version": "1.0",
                "command-line": "tool [X]",
                "inputs": [
                    {"id": "x", "name": "X", "type": "String", "value-key": "[X]"}
                ],
                "container-image": {"type": "docker", "image": "example/tool"},
            }
        )
    )
    inv_path = tmp_path / "inv.json"
    inv_path.write_text('{"x": "v"}')

    result = CliRunner().invoke(
        app,
        [
            "exec",
            "launch",
            str(descriptor_path),
            str(inv_path),
            "--force-docker",
            "--force-singularity",
        ],
    )
    assert result.exit_code == 1
    combined = (result.stdout or "") + (result.stderr or "")
    assert "at most one" in combined


def test_cli_simulate_accepts_i_flag(tmp_path):
    """Classic-bosh -i should provide the invocation as an alternative to positional."""
    import json

    from typer.testing import CliRunner

    from boutiques.cli import app

    descriptor_path = tmp_path / "descriptor.json"
    descriptor_path.write_text(
        json.dumps(
            {
                "schema-version": "0.5",
                "name": "t",
                "description": "x",
                "tool-version": "1.0",
                "command-line": "tool [X]",
                "inputs": [
                    {"id": "x", "name": "X", "type": "String", "value-key": "[X]"}
                ],
            }
        )
    )
    inv_path = tmp_path / "inv.json"
    inv_path.write_text('{"x": "hello"}')

    result = CliRunner().invoke(
        app, ["exec", "simulate", str(descriptor_path), "-i", str(inv_path)]
    )
    assert result.exit_code == 0
    assert "hello" in result.stdout


def test_cli_simulate_both_positional_and_i_errors(tmp_path):
    import json

    from typer.testing import CliRunner

    from boutiques.cli import app

    descriptor_path = tmp_path / "descriptor.json"
    descriptor_path.write_text(
        json.dumps(
            {
                "schema-version": "0.5",
                "name": "t",
                "description": "x",
                "tool-version": "1.0",
                "command-line": "tool [X]",
                "inputs": [
                    {"id": "x", "name": "X", "type": "String", "value-key": "[X]"}
                ],
            }
        )
    )
    inv_path = tmp_path / "inv.json"
    inv_path.write_text('{"x": "v"}')

    result = CliRunner().invoke(
        app,
        ["exec", "simulate", str(descriptor_path), str(inv_path), "-i", str(inv_path)],
    )
    assert result.exit_code == 1
    combined = (result.stdout or "") + (result.stderr or "")
    assert "not both" in combined


def test_unknown_runtime_raises():
    descriptor = _echo_descriptor()
    with pytest.raises(RuntimeError_, match="Unknown runtime"):
        launch(
            descriptor,
            {"python": "p", "script": "s", "msg": "m"},
            runtime="podman",
        )


def test_output_paths_resolve_against_cwd(tmp_path):
    """Path-template substitution + existence check (no subprocess)."""
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
            "output-files": [{"id": "out", "name": "Out", "path-template": "[NAME].txt"}],
        }
    )
    (tmp_path / "result.txt").write_text("data")

    from boutiques.execution.outputs import resolve_output_paths

    outputs = resolve_output_paths(descriptor, {"name": "result"}, tmp_path)
    assert len(outputs) == 1
    assert outputs[0].path == (tmp_path / "result.txt").resolve()
    assert outputs[0].exists


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
            "environment-variables": [{"name": "BOUTIQUES_TEST_VAR", "value": "from_descriptor"}],
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
        stream=False,
    )
    assert result.exit_code == 0
    assert "from_descriptor" in result.stdout
