"""Tests for cross-field semantic validation."""

from boutiques.loader import load
from boutiques.semantic import check
from boutiques.validate import validate


def _make(name="t", **overrides):
    """Minimal v0.5 descriptor — overrides merged into the base."""
    base = {
        "schema-version": "0.5",
        "name": name,
        "description": "Test tool",
        "tool-version": "1.0",
        "command-line": "tool [X]",
        "inputs": [
            {
                "id": "x",
                "name": "X",
                "type": "String",
                "value-key": "[X]",
            }
        ],
    }
    base.update(overrides)
    return load(base)


# ---- per-input dependency checks ------------------------------------------


def test_clean_descriptor_has_no_semantic_errors():
    assert check(_make()) == []


def test_exclusive_minimum_requires_minimum():
    d = _make(
        **{
            "command-line": "tool [N]",
            "inputs": [
                {
                    "id": "n",
                    "name": "N",
                    "type": "Number",
                    "value-key": "[N]",
                    "exclusive-minimum": True,
                }
            ],
        }
    )
    errors = check(d)
    assert any("exclusive-minimum" in str(e) for e in errors)


def test_list_separator_requires_list():
    d = _make(
        **{
            "inputs": [
                {
                    "id": "x",
                    "name": "X",
                    "type": "String",
                    "value-key": "[X]",
                    "list-separator": ",",
                }
            ],
        }
    )
    errors = check(d)
    assert any("list-separator" in str(e) and "list" in str(e) for e in errors)


def test_command_line_flag_separator_requires_command_line_flag():
    d = _make(
        **{
            "inputs": [
                {
                    "id": "x",
                    "name": "X",
                    "type": "String",
                    "value-key": "[X]",
                    "command-line-flag-separator": "=",
                }
            ],
        }
    )
    errors = check(d)
    assert any("command-line-flag-separator" in str(e) for e in errors)


def test_min_greater_than_max_is_an_error():
    d = _make(
        **{
            "command-line": "tool [N]",
            "inputs": [
                {
                    "id": "n",
                    "name": "N",
                    "type": "Number",
                    "value-key": "[N]",
                    "minimum": 10,
                    "maximum": 5,
                }
            ],
        }
    )
    errors = check(d)
    assert any("minimum" in str(e) and "<=" in str(e) for e in errors)


def test_min_list_greater_than_max_list_is_an_error():
    d = _make(
        **{
            "inputs": [
                {
                    "id": "x",
                    "name": "X",
                    "type": "String",
                    "value-key": "[X]",
                    "list": True,
                    "min-list-entries": 5,
                    "max-list-entries": 2,
                }
            ],
        }
    )
    errors = check(d)
    assert any("min-list-entries" in str(e) for e in errors)


def test_value_disables_requires_value_choices():
    d = _make(
        **{
            "inputs": [
                {
                    "id": "x",
                    "name": "X",
                    "type": "String",
                    "value-key": "[X]",
                    "value-disables": {"foo": ["y"]},
                }
            ],
        }
    )
    errors = check(d)
    assert any("value-disables" in str(e) for e in errors)


# ---- descriptor-wide checks -----------------------------------------------


def test_duplicate_input_ids_flagged():
    d = _make(
        **{
            "command-line": "tool [X] [Y]",
            "inputs": [
                {"id": "x", "name": "X", "type": "String", "value-key": "[X]"},
                {"id": "x", "name": "X2", "type": "String", "value-key": "[Y]"},
            ],
        }
    )
    errors = check(d)
    assert any("Duplicate input id" in str(e) for e in errors)


def test_duplicate_value_keys_flagged():
    d = _make(
        **{
            "command-line": "tool [X]",
            "inputs": [
                {"id": "a", "name": "A", "type": "String", "value-key": "[X]"},
                {"id": "b", "name": "B", "type": "String", "value-key": "[X]"},
            ],
        }
    )
    errors = check(d)
    assert any("Duplicate value-key" in str(e) for e in errors)


def test_value_key_not_in_command_line_flagged():
    d = _make(
        **{
            "command-line": "tool ",  # missing [X]
            "inputs": [
                {"id": "x", "name": "X", "type": "String", "value-key": "[X]"},
            ],
        }
    )
    errors = check(d)
    assert any("does not appear in the command-line" in str(e) for e in errors)


def test_group_member_must_reference_existing_input():
    d = _make(
        **{
            "groups": [{"id": "g", "name": "G", "members": ["x", "does_not_exist"]}],
        }
    )
    errors = check(d)
    assert any("unknown input id" in str(e) for e in errors)


def test_duplicate_output_ids_flagged():
    d = _make(
        **{
            "output-files": [
                {"id": "o", "name": "O", "path-template": "a.txt"},
                {"id": "o", "name": "O2", "path-template": "b.txt"},
            ],
        }
    )
    errors = check(d)
    assert any("Duplicate output id" in str(e) for e in errors)


# ---- sub-command recursion ------------------------------------------------


def test_subcommand_union_inherits_semantic_checks():
    raw = {
        "schema-version": "0.5+styx",
        "name": "t",
        "tool-version": "0.1",
        "description": "test",
        "command-line": "t [OP]",
        "inputs": [
            {
                "id": "op",
                "name": "OP",
                "value-key": "[OP]",
                "type": [
                    {
                        "id": "first",
                        "command-line": "first [A]",
                        "inputs": [
                            {
                                "id": "a",
                                "name": "A",
                                "type": "Number",
                                "value-key": "[A]",
                                "exclusive-minimum": True,  # requires minimum
                            }
                        ],
                    }
                ],
            }
        ],
    }
    errors = check(load(raw))
    assert any("exclusive-minimum" in str(e) for e in errors)


# ---- integration with validate() -------------------------------------------


def test_validate_surfaces_semantic_errors():
    d_dict = {
        "schema-version": "0.5",
        "name": "t",
        "description": "test",
        "tool-version": "1.0",
        "command-line": "tool [X] [X]",  # forces duplicate value-key usage
        "inputs": [
            {"id": "a", "name": "A", "type": "String", "value-key": "[X]"},
            {"id": "b", "name": "B", "type": "String", "value-key": "[X]"},
        ],
    }
    result = validate(d_dict)
    assert not result.ok
    assert any("Duplicate value-key" in str(e) for e in result.errors)
