"""Tests for output path resolution, including conditional templates."""

from __future__ import annotations

from pathlib import Path

import pytest

from boutiques.execution.outputs import resolve_output_paths
from boutiques.loader import load


def _descriptor(*, output, inputs=None, cli="tool [P]"):
    inputs = inputs or [{"id": "p", "name": "P", "type": "Number", "value-key": "[P]"}]
    return load(
        {
            "schema-version": "0.5",
            "name": "t",
            "description": "x",
            "tool-version": "1.0",
            "command-line": cli,
            "inputs": inputs,
            "output-files": [output],
        }
    )


def test_conditional_path_template_picks_matching_branch(tmp_path):
    descriptor = _descriptor(
        output={
            "id": "out",
            "name": "Out",
            "conditional-path-template": [
                {"[P] > 8": "outputs/big.txt"},
                {"[P] <= 8": "outputs/small.txt"},
            ],
        }
    )
    outputs = resolve_output_paths(descriptor, {"p": 10}, tmp_path)
    assert outputs[0].path == (tmp_path / "outputs" / "big.txt").resolve()


def test_conditional_path_template_falls_through_to_default(tmp_path):
    descriptor = _descriptor(
        output={
            "id": "out",
            "name": "Out",
            "conditional-path-template": [
                {"[P] > 100": "outputs/big.txt"},
                {"default": "outputs/default.txt"},
            ],
        }
    )
    outputs = resolve_output_paths(descriptor, {"p": 5}, tmp_path)
    assert outputs[0].path == (tmp_path / "outputs" / "default.txt").resolve()


def test_conditional_path_template_no_match_no_default(tmp_path):
    descriptor = _descriptor(
        output={
            "id": "out",
            "name": "Out",
            "conditional-path-template": [
                {"[P] > 100": "outputs/big.txt"},
                {"[P] < -100": "outputs/small.txt"},
            ],
        }
    )
    outputs = resolve_output_paths(descriptor, {"p": 5}, tmp_path)
    assert outputs[0].path is None


def test_conditional_path_template_supports_logical_ops(tmp_path):
    descriptor = _descriptor(
        output={
            "id": "out",
            "name": "Out",
            "conditional-path-template": [
                {"[P] > 0 and [P] < 10": "outputs/single_digit.txt"},
                {"default": "outputs/other.txt"},
            ],
        }
    )
    outputs = resolve_output_paths(descriptor, {"p": 5}, tmp_path)
    assert outputs[0].path.name == "single_digit.txt"


def test_conditional_path_template_handles_string_choice(tmp_path):
    descriptor = _descriptor(
        cli="tool [MODE]",
        inputs=[
            {
                "id": "mode",
                "name": "Mode",
                "type": "String",
                "value-key": "[MODE]",
                "value-choices": ["fast", "slow"],
            }
        ],
        output={
            "id": "out",
            "name": "Out",
            "conditional-path-template": [
                {"[MODE] == 'fast'": "fast_result.txt"},
                {"[MODE] == 'slow'": "slow_result.txt"},
            ],
        },
    )
    outputs = resolve_output_paths(descriptor, {"mode": "fast"}, tmp_path)
    assert outputs[0].path.name == "fast_result.txt"


def test_conditional_path_template_rejects_unsafe_expression(tmp_path):
    descriptor = _descriptor(
        output={
            "id": "out",
            "name": "Out",
            "conditional-path-template": [
                {"__import__('os').system('echo hi')": "x.txt"},
            ],
        }
    )
    with pytest.raises(ValueError, match="Disallowed expression element"):
        resolve_output_paths(descriptor, {"p": 5}, tmp_path)
