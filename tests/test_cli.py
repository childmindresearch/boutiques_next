from pathlib import Path

from typer.testing import CliRunner

from boutiques import __version__
from boutiques.cli import app

runner = CliRunner()

FIXTURES = Path(__file__).parent / "fixtures"


def test_help_lists_subcommands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("validate", "example", "exec", "version"):
        assert cmd in result.stdout


def test_version_prints_package_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_validate_ok():
    result = runner.invoke(app, ["validate", str(FIXTURES / "v_0_5" / "fsl_bet.json")])
    assert result.exit_code == 0
    assert "OK" in result.stdout


def test_validate_fails_for_bad_descriptor(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text('{"schema-version": "0.5"}')  # missing required fields
    result = runner.invoke(app, ["validate", str(bad)])
    assert result.exit_code != 0
