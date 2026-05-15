"""Tests for runtime invocation enforcement."""

from __future__ import annotations

import pytest

from boutiques.execution import resolve
from boutiques.invocation_check import (
    InvocationValidationError,
    validate_invocation,
)
from boutiques.loader import load


def _make(*, command_line="tool [X]", inputs=None, groups=None):
    inputs = inputs or [
        {"id": "x", "name": "X", "type": "String", "value-key": "[X]"}
    ]
    descriptor = {
        "schema-version": "0.5",
        "name": "t",
        "description": "x",
        "tool-version": "1.0",
        "command-line": command_line,
        "inputs": inputs,
    }
    if groups is not None:
        descriptor["groups"] = groups
    return load(descriptor)


# ---- Pydantic-level range and list bounds --------------------------------


def test_numeric_minimum_enforced():
    d = _make(
        command_line="tool [N]",
        inputs=[
            {
                "id": "n",
                "name": "N",
                "type": "Number",
                "value-key": "[N]",
                "minimum": 0,
                "maximum": 1,
            }
        ],
    )
    errs = validate_invocation(d, {"n": -0.5})
    assert any("greater than or equal to" in str(e) for e in errs)


def test_numeric_exclusive_minimum_enforced():
    d = _make(
        command_line="tool [N]",
        inputs=[
            {
                "id": "n",
                "name": "N",
                "type": "Number",
                "value-key": "[N]",
                "minimum": 0,
                "exclusive-minimum": True,
            }
        ],
    )
    errs = validate_invocation(d, {"n": 0})
    assert any("greater than 0" in str(e) for e in errs)


def test_list_min_entries_enforced():
    d = _make(
        command_line="tool [L]",
        inputs=[
            {
                "id": "l",
                "name": "L",
                "type": "Number",
                "value-key": "[L]",
                "list": True,
                "min-list-entries": 3,
            }
        ],
    )
    errs = validate_invocation(d, {"l": [1.0, 2.0]})
    assert any("at least 3" in str(e) for e in errs)


def test_list_max_entries_enforced():
    d = _make(
        command_line="tool [L]",
        inputs=[
            {
                "id": "l",
                "name": "L",
                "type": "Number",
                "value-key": "[L]",
                "list": True,
                "max-list-entries": 2,
            }
        ],
    )
    errs = validate_invocation(d, {"l": [1.0, 2.0, 3.0]})
    assert any("at most 2" in str(e) for e in errs)


def test_value_choices_already_enforced_via_literal():
    d = _make(
        inputs=[
            {
                "id": "x",
                "name": "X",
                "type": "String",
                "value-key": "[X]",
                "value-choices": ["alpha", "beta"],
            }
        ],
    )
    errs = validate_invocation(d, {"x": "gamma"})
    assert any("'alpha'" in str(e) and "'beta'" in str(e) for e in errs)


# ---- Cross-input: requires-inputs / disables-inputs ----------------------


def test_requires_inputs_satisfied():
    d = _make(
        command_line="tool [A] [B]",
        inputs=[
            {
                "id": "a",
                "name": "A",
                "type": "Flag",
                "command-line-flag": "-a",
                "value-key": "[A]",
                "requires-inputs": ["b"],
            },
            {
                "id": "b",
                "name": "B",
                "type": "String",
                "value-key": "[B]",
                "optional": True,
            },
        ],
    )
    assert validate_invocation(d, {"a": True, "b": "value"}) == []


def test_requires_inputs_missing_dependency_flagged():
    d = _make(
        command_line="tool [A] [B]",
        inputs=[
            {
                "id": "a",
                "name": "A",
                "type": "Flag",
                "command-line-flag": "-a",
                "value-key": "[A]",
                "requires-inputs": ["b"],
            },
            {
                "id": "b",
                "name": "B",
                "type": "String",
                "value-key": "[B]",
                "optional": True,
            },
        ],
    )
    errs = validate_invocation(d, {"a": True})
    assert any("requires 'b'" in str(e) for e in errs)


def test_disables_inputs_conflict_flagged():
    d = _make(
        command_line="tool [A] [B]",
        inputs=[
            {
                "id": "a",
                "name": "A",
                "type": "Flag",
                "command-line-flag": "-a",
                "value-key": "[A]",
                "disables-inputs": ["b"],
            },
            {
                "id": "b",
                "name": "B",
                "type": "Flag",
                "command-line-flag": "-b",
                "value-key": "[B]",
            },
        ],
    )
    errs = validate_invocation(d, {"a": True, "b": True})
    assert any("disables 'b'" in str(e) for e in errs)


def test_inactive_flag_does_not_trigger_requires():
    """A Flag with value=False is inactive — its requires-inputs don't apply."""
    d = _make(
        command_line="tool [A] [B]",
        inputs=[
            {
                "id": "a",
                "name": "A",
                "type": "Flag",
                "command-line-flag": "-a",
                "value-key": "[A]",
                "requires-inputs": ["b"],
            },
            {
                "id": "b",
                "name": "B",
                "type": "String",
                "value-key": "[B]",
                "optional": True,
            },
        ],
    )
    assert validate_invocation(d, {"a": False}) == []


# ---- value-requires / value-disables -------------------------------------


def test_value_requires_for_active_choice():
    d = _make(
        command_line="tool [MODE] [OPT]",
        inputs=[
            {
                "id": "mode",
                "name": "Mode",
                "type": "String",
                "value-key": "[MODE]",
                "value-choices": ["fast", "slow"],
                "value-requires": {"slow": ["opt"]},
            },
            {
                "id": "opt",
                "name": "Opt",
                "type": "String",
                "value-key": "[OPT]",
                "optional": True,
            },
        ],
    )
    errs = validate_invocation(d, {"mode": "slow"})
    assert any("requires 'opt'" in str(e) for e in errs)
    assert validate_invocation(d, {"mode": "fast"}) == []


def test_value_disables_for_active_choice():
    d = _make(
        command_line="tool [MODE] [VERB]",
        inputs=[
            {
                "id": "mode",
                "name": "Mode",
                "type": "String",
                "value-key": "[MODE]",
                "value-choices": ["quiet", "loud"],
                "value-disables": {"quiet": ["verb"]},
            },
            {
                "id": "verb",
                "name": "Verbose",
                "type": "Flag",
                "command-line-flag": "-v",
                "value-key": "[VERB]",
            },
        ],
    )
    errs = validate_invocation(d, {"mode": "quiet", "verb": True})
    assert any("disables 'verb'" in str(e) for e in errs)


# ---- Groups --------------------------------------------------------------


def test_mutually_exclusive_violation():
    d = _make(
        command_line="tool [A] [B]",
        inputs=[
            {
                "id": "a",
                "name": "A",
                "type": "Flag",
                "command-line-flag": "-a",
                "value-key": "[A]",
            },
            {
                "id": "b",
                "name": "B",
                "type": "Flag",
                "command-line-flag": "-b",
                "value-key": "[B]",
            },
        ],
        groups=[
            {"id": "g", "name": "G", "members": ["a", "b"], "mutually-exclusive": True}
        ],
    )
    errs = validate_invocation(d, {"a": True, "b": True})
    assert any("mutually-exclusive" in str(e) for e in errs)


def test_one_is_required_violation():
    d = _make(
        command_line="tool [A] [B]",
        inputs=[
            {
                "id": "a",
                "name": "A",
                "type": "Flag",
                "command-line-flag": "-a",
                "value-key": "[A]",
            },
            {
                "id": "b",
                "name": "B",
                "type": "Flag",
                "command-line-flag": "-b",
                "value-key": "[B]",
            },
        ],
        groups=[
            {"id": "g", "name": "G", "members": ["a", "b"], "one-is-required": True}
        ],
    )
    errs = validate_invocation(d, {"a": False, "b": False})
    assert any("at least one active member" in str(e) for e in errs)


def test_all_or_none_partial_violation():
    d = _make(
        command_line="tool [A] [B] [C]",
        inputs=[
            {
                "id": "a",
                "name": "A",
                "type": "String",
                "value-key": "[A]",
                "optional": True,
            },
            {
                "id": "b",
                "name": "B",
                "type": "String",
                "value-key": "[B]",
                "optional": True,
            },
            {
                "id": "c",
                "name": "C",
                "type": "String",
                "value-key": "[C]",
                "optional": True,
            },
        ],
        groups=[
            {
                "id": "g",
                "name": "G",
                "members": ["a", "b", "c"],
                "all-or-none": True,
            }
        ],
    )
    errs = validate_invocation(d, {"a": "1", "b": "2"})
    assert any("all-or-none" in str(e) for e in errs)
    assert validate_invocation(d, {"a": "1", "b": "2", "c": "3"}) == []
    assert validate_invocation(d, {}) == []


# ---- SubCommand recursion ------------------------------------------------


def test_requires_inputs_inside_subcommand():
    d = load(
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
                            "id": "do",
                            "command-line": "do [A] [B]",
                            "inputs": [
                                {
                                    "id": "a",
                                    "name": "A",
                                    "type": "Flag",
                                    "command-line-flag": "-a",
                                    "value-key": "[A]",
                                    "requires-inputs": ["b"],
                                },
                                {
                                    "id": "b",
                                    "name": "B",
                                    "type": "String",
                                    "value-key": "[B]",
                                    "optional": True,
                                },
                            ],
                        }
                    ],
                }
            ],
        }
    )
    errs = validate_invocation(d, {"op": {"id": "do", "a": True}})
    assert any("requires 'b'" in str(e) for e in errs)


# ---- Resolve integration -------------------------------------------------


def test_resolve_raises_on_cross_input_violation():
    d = _make(
        command_line="tool [A] [B]",
        inputs=[
            {
                "id": "a",
                "name": "A",
                "type": "Flag",
                "command-line-flag": "-a",
                "value-key": "[A]",
                "disables-inputs": ["b"],
            },
            {
                "id": "b",
                "name": "B",
                "type": "Flag",
                "command-line-flag": "-b",
                "value-key": "[B]",
            },
        ],
    )
    with pytest.raises(InvocationValidationError, match="disables"):
        resolve(d, {"a": True, "b": True})


def test_resolve_raises_on_numeric_range_violation():
    d = _make(
        command_line="tool [N]",
        inputs=[
            {
                "id": "n",
                "name": "N",
                "type": "Number",
                "value-key": "[N]",
                "minimum": 0,
                "maximum": 10,
            }
        ],
    )
    with pytest.raises(InvocationValidationError, match="less than or equal to"):
        resolve(d, {"n": 100})


def test_cli_launch_reports_missing_binary_cleanly(tmp_path):
    """A missing command should surface a clean Runtime error, not a traceback."""
    import json

    from typer.testing import CliRunner

    from boutiques.cli import app

    descriptor_path = tmp_path / "descriptor.json"
    descriptor_path.write_text(
        json.dumps(
            {
                "schema-version": "0.5",
                "name": "missing_tool",
                "description": "x",
                "tool-version": "1.0",
                "command-line": "definitely_not_a_real_binary_xyz123 [X]",
                "inputs": [
                    {"id": "x", "name": "X", "type": "String", "value-key": "[X]"},
                ],
            }
        )
    )
    inv_path = tmp_path / "inv.json"
    inv_path.write_text('{"x": "v"}')

    result = CliRunner().invoke(
        app, ["exec", "launch", str(descriptor_path), str(inv_path), "--cwd", str(tmp_path)]
    )
    assert result.exit_code == 2
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Command not found" in combined
    assert "Traceback" not in combined


def test_cli_simulate_reports_invocation_error_cleanly(tmp_path):
    """The CLI must report invocation errors as text + exit 1, not crash."""
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
                "command-line": "tool [N]",
                "inputs": [
                    {
                        "id": "n",
                        "name": "N",
                        "type": "Number",
                        "value-key": "[N]",
                        "minimum": 0,
                        "maximum": 1,
                    }
                ],
            }
        )
    )
    inv_path = tmp_path / "inv.json"
    inv_path.write_text('{"n": 2.0}')

    result = CliRunner().invoke(
        app, ["exec", "simulate", str(descriptor_path), str(inv_path)]
    )
    assert result.exit_code == 1
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Invocation invalid" in combined
    assert "Traceback" not in combined
