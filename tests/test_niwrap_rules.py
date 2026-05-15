"""Validation rules ported from niwrap's boutiques tooling tests.

Two hard semantic errors (duplicate path-templates, orphan command-line
tokens) plus three lint warnings (value-key format convention,
path-template safety, duplicate ``[KEY]`` in command-line).
"""

from __future__ import annotations

from boutiques.lint import lint
from boutiques.loader import load
from boutiques.semantic import check


def _make(**overrides):
    base = {
        "schema-version": "0.5",
        "name": "t",
        "description": "x",
        "tool-version": "1.0",
        "command-line": "tool [X]",
        "inputs": [
            {"id": "x", "name": "X", "type": "String", "value-key": "[X]"},
        ],
    }
    base.update(overrides)
    return load(base)


# ---- Semantic: duplicate path-templates ----------------------------------


def test_duplicate_path_template_is_an_error():
    d = _make(
        **{
            "output-files": [
                {"id": "a", "name": "A", "path-template": "out.txt"},
                {"id": "b", "name": "B", "path-template": "out.txt"},
            ],
        }
    )
    errors = check(d)
    assert any("Duplicate path-template" in str(e) for e in errors)


def test_distinct_path_templates_are_fine():
    d = _make(
        **{
            "output-files": [
                {"id": "a", "name": "A", "path-template": "a.txt"},
                {"id": "b", "name": "B", "path-template": "b.txt"},
            ],
        }
    )
    assert not any("Duplicate path-template" in str(e) for e in check(d))


# ---- Semantic: orphan [UPPER_CASE] tokens in command-line ----------------


def test_orphan_command_line_token_is_an_error():
    d = _make(
        **{
            "command-line": "tool [X] [Y]",  # [Y] has no matching input value-key
        }
    )
    errors = check(d)
    assert any("[Y]" in str(e) and "no matching" in str(e) for e in errors)


def test_lowercase_pseudo_tokens_are_not_flagged_as_orphans():
    """Only [UPPER_CASE] forms count; other bracketed strings are tool literals."""
    d = _make(
        **{
            "command-line": "tool [X] [example-text-not-a-token]",
        }
    )
    errors = check(d)
    assert not any("no matching" in str(e) for e in errors)


# ---- Lint: value-key format convention -----------------------------------


def test_lowercase_value_key_lints_as_convention_warning():
    d = _make(
        **{
            "command-line": "tool [x]",  # lowercase value-key
            "inputs": [
                {"id": "x", "name": "X", "type": "String", "value-key": "[x]"},
            ],
        }
    )
    issues = lint(d)
    assert any("value-key" in i.field and "UPPER_CASE" in i.message for i in issues)


def test_conventional_value_key_does_not_lint():
    issues = lint(_make())
    assert not any("UPPER_CASE" in i.message for i in issues)


# ---- Lint: Windows-unsafe path-template chars ----------------------------


def test_path_template_with_unsafe_chars_lints():
    d = _make(
        **{
            "output-files": [
                {"id": "a", "name": "A", "path-template": "out:dir/result.txt"},
            ],
        }
    )
    issues = lint(d)
    assert any("Windows" in i.message for i in issues)


def test_path_template_safe_chars_does_not_lint():
    d = _make(
        **{
            "output-files": [
                {"id": "a", "name": "A", "path-template": "outputs/result.txt"},
            ],
        }
    )
    issues = lint(d)
    assert not any("Windows" in i.message for i in issues)


# ---- Lint: duplicate [KEY] in command-line -------------------------------


def test_repeated_token_in_command_line_lints():
    d = _make(
        **{
            "command-line": "tool [X] [X]",  # X appears twice
            "inputs": [
                {"id": "x", "name": "X", "type": "String", "value-key": "[X]"},
            ],
        }
    )
    issues = lint(d)
    assert any("appears 2 times" in i.message for i in issues)


def test_single_token_does_not_lint():
    issues = lint(_make())
    assert not any("appears" in i.message and "times" in i.message for i in issues)


# ---- Sub-command recursion ------------------------------------------------


def test_orphan_token_inside_subcommand_is_an_error():
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
                            "id": "first",
                            "command-line": "first [GHOST]",  # [GHOST] has no input
                            "inputs": [
                                {
                                    "id": "a",
                                    "name": "A",
                                    "type": "String",
                                    "value-key": "[A]",
                                }
                            ],
                        }
                    ],
                }
            ],
        }
    )
    errors = check(d)
    assert any("[GHOST]" in str(e) for e in errors)
