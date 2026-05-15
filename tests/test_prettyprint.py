"""Tests for ``bosh pprint`` / ``boutiques.prettyprint``."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from typer.testing import CliRunner

from boutiques.cli import app
from boutiques.loader import load
from boutiques.prettyprint import pprint

FIXTURES = Path(__file__).parent / "fixtures"


def _render(descriptor) -> str:
    """Render a descriptor with rich into a captured string."""
    console = Console(record=True, width=100, force_terminal=False, color_system=None)
    pprint(descriptor, console=console)
    return console.export_text()


def test_renders_basic_fields():
    descriptor = load(FIXTURES / "v05" / "fsl_bet.json")
    output = _render(descriptor)
    assert "fsl_bet" in output
    assert "v1.0.0" in output
    assert "command-line" in output
    assert "bet [INPUT_FILE]" in output


def test_lists_every_input_id():
    descriptor = load(FIXTURES / "v05" / "fsl_bet.json")
    output = _render(descriptor)
    for inp in descriptor.inputs:
        assert inp.id in output


def test_includes_input_count():
    descriptor = load(FIXTURES / "v05" / "fsl_bet.json")
    output = _render(descriptor)
    assert f"inputs ({len(descriptor.inputs)})" in output


def test_marks_required_and_optional():
    descriptor = load(FIXTURES / "v05" / "fsl_bet.json")
    output = _render(descriptor)
    assert "required" in output
    assert "optional" in output


def test_shows_container_image():
    descriptor = load(FIXTURES / "v05" / "fsl_bet.json")
    output = _render(descriptor)
    assert "container" in output
    assert "docker" in output


def test_shows_numeric_ranges():
    """fsl_bet's fractional_intensity has minimum=0, maximum=1."""
    descriptor = load(FIXTURES / "v05" / "fsl_bet.json")
    output = _render(descriptor)
    assert "range: [0" in output


def test_renders_subcommand_union():
    descriptor = load(FIXTURES / "v05_styx" / "subcommand_union.json")
    output = _render(descriptor)
    assert "SubCommandUnion" in output
    # Both candidates appear, each with its own command-line
    assert "blur" in output
    assert "sharpen" in output
    assert "blur [SIGMA]" in output
    assert "sharpen [AMOUNT]" in output


def test_renders_list_bounds():
    descriptor = load(FIXTURES / "v05_styx" / "subcommand_union.json")
    output = _render(descriptor)
    assert "list:" in output
    assert "separator=" in output


def test_renders_niwrap_style_with_stdio_outputs():
    descriptor = load(FIXTURES / "v05_styx" / "niwrap_style.json")
    output = _render(descriptor)
    assert "@2dwarper" in output
    # niwrap-style has tool-version absent; should still render
    assert "v" in output  # the header line


def test_cli_exits_zero_and_prints():
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["pprint", "--no-color", str(FIXTURES / "v05" / "fsl_bet.json")],
    )
    assert result.exit_code == 0
    assert "fsl_bet" in result.stdout


def test_cli_handles_invalid_descriptor(tmp_path):
    runner = CliRunner()
    bad = tmp_path / "bad.json"
    bad.write_text('{"schema-version": "9.9"}')
    result = runner.invoke(app, ["pprint", str(bad)])
    assert result.exit_code != 0
