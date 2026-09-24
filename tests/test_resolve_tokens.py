"""Token-level resolver tests covering shell-safety and embedded value-keys."""

from boutiques.execution import resolve, simulate
from boutiques.loader import load_descriptor


def _descriptor(inputs, command_line="tool [X]", schema_version="0.5"):
    return load_descriptor(
        {
            "schema-version": schema_version,
            "name": "t",
            "description": "test",
            "tool-version": "1.0",
            "command-line": command_line,
            "inputs": inputs,
        }
    )


def test_resolve_returns_token_list():
    d = _descriptor([{"id": "x", "name": "X", "type": "String", "value-key": "[X]"}])
    assert resolve(d, {"x": "hello"}) == ["tool", "hello"]


def test_value_with_space_stays_one_token():
    """Old string-resolve would silently split this into two argv entries."""
    d = _descriptor([{"id": "x", "name": "X", "type": "String", "value-key": "[X]"}])
    tokens = resolve(d, {"x": "hello world"})
    assert tokens == ["tool", "hello world"]
    # Display string quotes for shell-safety
    assert simulate(d, {"x": "hello world"}) == "tool 'hello world'"


def test_flag_with_space_separator_emits_two_tokens():
    d = _descriptor(
        [
            {
                "id": "x",
                "name": "X",
                "type": "Number",
                "value-key": "[X]",
                "command-line-flag": "-f",
            }
        ]
    )
    assert resolve(d, {"x": 0.5}) == ["tool", "-f", "0.5"]


def test_flag_with_equals_separator_glues_into_one_token():
    d = _descriptor(
        [
            {
                "id": "x",
                "name": "X",
                "type": "String",
                "value-key": "[X]",
                "command-line-flag": "--input",
                "command-line-flag-separator": "=",
            }
        ]
    )
    assert resolve(d, {"x": "val"}) == ["tool", "--input=val"]


def test_list_with_space_separator_is_per_item_tokens():
    d = _descriptor(
        [
            {
                "id": "x",
                "name": "X",
                "type": "Number",
                "value-key": "[X]",
                "command-line-flag": "-c",
                "list": True,
            }
        ]
    )
    assert resolve(d, {"x": [1.0, 2.0, 3.0]}) == ["tool", "-c", "1.0", "2.0", "3.0"]


def test_list_with_comma_separator_is_one_token():
    d = _descriptor(
        [
            {
                "id": "x",
                "name": "X",
                "type": "Number",
                "value-key": "[X]",
                "list": True,
                "list-separator": ",",
            }
        ]
    )
    assert resolve(d, {"x": [1.0, 2.0, 3.0]}) == ["tool", "1.0,2.0,3.0"]


def test_embedded_value_key_substitutes_within_token():
    """A value-key inside a larger template token uses scalar substitution."""
    d = _descriptor(
        [{"id": "x", "name": "X", "type": "String", "value-key": "[X]"}],
        command_line="tool --input=[X]",
    )
    assert resolve(d, {"x": "val"}) == ["tool", "--input=val"]


def test_optional_omitted_input_drops_token():
    d = _descriptor(
        [
            {
                "id": "x",
                "name": "X",
                "type": "String",
                "value-key": "[X]",
                "optional": True,
            }
        ]
    )
    # No value provided; the value-key token vanishes entirely.
    assert resolve(d, {}) == ["tool"]


def _repeatable_subcommand(command_line="tool [C]", input_extra=None):
    """Flag-bearing repeatable sub-command; extra input kwargs merged in."""
    base = {
        "id": "c",
        "name": "C",
        "value-key": "[C]",
        "command-line-flag": "--config",
        "optional": True,
        "list": True,
        "type": {
            "id": "cfg",
            "command-line": "[K] [V]",
            "inputs": [
                {"id": "k", "name": "K", "type": "String", "value-key": "[K]"},
                {"id": "v", "name": "V", "type": "String", "value-key": "[V]"},
            ],
        },
    }
    if input_extra:
        base.update(input_extra)
    return _descriptor([base], command_line=command_line, schema_version="0.5+styx")


def test_repeatable_subcommand_flag_emitted_once():
    """A parent flag on a list sub-command prefixes the whole repeated block
    (styx: optional(sequence(flag, repeat(...))))."""
    d = _repeatable_subcommand()
    tokens = resolve(
        d,
        {"c": [{"k": "a", "v": "1"}, {"k": "b", "v": "2"}]},
    )
    assert tokens == ["tool", "--config", "a", "1", "b", "2"]


def test_repeatable_subcommand_custom_separator_joins_one_token():
    """A custom list-separator fuses the repeated blocks into a single token."""
    d = _repeatable_subcommand(input_extra={"list-separator": "+"})
    tokens = resolve(
        d,
        {"c": [{"k": "a", "v": "1"}, {"k": "b", "v": "2"}]},
    )
    assert tokens == ["tool", "--config", "a 1+b 2"]


def test_repeatable_subcommand_omitted_drops_token():
    d = _repeatable_subcommand()
    assert resolve(d, {}) == ["tool"]
