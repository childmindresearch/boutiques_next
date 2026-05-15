"""Tests for file-input mount planning."""

from __future__ import annotations

from unittest.mock import patch

from boutiques.execution import launch
from boutiques.execution.mounts import collect_file_mounts
from boutiques.execution.runtime.base import RunResult
from boutiques.loader import load


def _fake_run(captured: dict):
    def _impl(argv, **kwargs):
        captured["argv"] = argv
        return RunResult(exit_code=0, stdout="", stderr="", duration_seconds=0.0)

    return _impl


def _descriptor_with_files(num_files: int = 2):
    return load(
        {
            "schema-version": "0.5",
            "name": "t",
            "description": "x",
            "tool-version": "1.0",
            "command-line": " ".join(f"[F{i}]" for i in range(num_files)),
            "inputs": [
                {
                    "id": f"f{i}",
                    "name": f"F{i}",
                    "type": "File",
                    "value-key": f"[F{i}]",
                }
                for i in range(num_files)
            ],
            "container-image": {"type": "docker", "image": "tool"},
        }
    )


def test_collect_file_mounts_returns_parent_dirs():
    descriptor = _descriptor_with_files(2)
    inv = {
        "f0": "/data/study/subject1/anat.nii.gz",
        "f1": "/scratch/work/output.txt",
    }
    mounts = collect_file_mounts(descriptor, inv)
    parents = {str(p) for p in mounts}
    assert any(p.endswith("subject1") for p in parents)
    assert any(p.endswith("work") for p in parents)


def test_collect_file_mounts_dedupes_descendants():
    descriptor = _descriptor_with_files(2)
    inv = {
        "f0": "/data/study/a.nii",
        "f1": "/data/study/sub/b.nii",
    }
    mounts = collect_file_mounts(descriptor, inv)
    # Only the broader /data/study should survive
    assert len(mounts) == 1
    assert str(mounts[0]).endswith("study")


def test_collect_file_mounts_handles_list_inputs():
    descriptor = load(
        {
            "schema-version": "0.5",
            "name": "t",
            "description": "x",
            "tool-version": "1.0",
            "command-line": "tool [VOLS]",
            "inputs": [
                {
                    "id": "vols",
                    "name": "V",
                    "type": "File",
                    "value-key": "[VOLS]",
                    "list": True,
                }
            ],
        }
    )
    mounts = collect_file_mounts(descriptor, {"vols": ["/a/x.nii", "/b/y.nii", "/a/sub/z.nii"]})
    parents = {p.name for p in mounts}
    assert "a" in parents
    assert "b" in parents
    assert len(mounts) == 2  # /a/sub is absorbed by /a


def test_collect_file_mounts_recurses_into_subcommand_union():
    descriptor = load(
        {
            "schema-version": "0.5+styx",
            "name": "t",
            "tool-version": "0.1",
            "description": "x",
            "command-line": "t [OP]",
            "inputs": [
                {
                    "id": "op",
                    "name": "OP",
                    "value-key": "[OP]",
                    "type": [
                        {
                            "id": "blur",
                            "command-line": "blur [IN]",
                            "inputs": [
                                {
                                    "id": "in",
                                    "name": "IN",
                                    "type": "File",
                                    "value-key": "[IN]",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    )
    mounts = collect_file_mounts(descriptor, {"op": {"id": "blur", "in": "/nested/file.nii"}})
    assert any(p.name == "nested" for p in mounts)


def test_docker_runtime_mounts_file_input_parents(tmp_path):
    """Real proof: file-input parent dirs become -v flags on docker run."""
    descriptor = _descriptor_with_files(2)
    inv = {
        "f0": "/data/study/a.nii",
        "f1": "/scratch/work/b.nii",
    }
    captured: dict = {}
    with patch(
        "boutiques.execution.runtime.docker.run_subprocess",
        side_effect=_fake_run(captured),
    ):
        launch(descriptor, inv, runtime="docker", cwd=tmp_path)

    argv = captured["argv"]
    # Every -v should be followed by host:container path
    mount_pairs = [argv[i + 1] for i, t in enumerate(argv) if t == "-v"]
    flat = " ".join(mount_pairs)
    assert "study" in flat
    assert "work" in flat
    # The cwd is also mounted
    assert str(tmp_path) in flat
