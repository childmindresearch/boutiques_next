from typer.testing import CliRunner

from boutiques import __version__
from boutiques.cli import app

runner = CliRunner()


def test_help_lists_subcommands():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for cmd in ("validate", "example", "exec", "version"):
        assert cmd in result.stdout


def test_version_prints_package_version():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout
