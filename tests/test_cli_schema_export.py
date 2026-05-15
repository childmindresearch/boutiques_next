"""Tests for ``bosh schema-export``."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from boutiques.cli import app
from boutiques.schema_export import VERSIONS

runner = CliRunner()


def test_default_writes_both_versions(tmp_path):
    target = tmp_path / "schema"
    result = runner.invoke(app, ["schema-export", "--output", str(target)])
    assert result.exit_code == 0
    for version in VERSIONS:
        path = target / version / "descriptor.schema.json"
        assert path.exists()
        # Sanity: valid JSON with the expected root keys
        schema = json.loads(path.read_text())
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert f"Wrote {path}" in result.stdout


def test_single_version_writes_one_file(tmp_path):
    target = tmp_path / "schema"
    result = runner.invoke(app, ["schema-export", "--output", str(target), "--version", "0.5"])
    assert result.exit_code == 0
    assert (target / "0.5" / "descriptor.schema.json").exists()
    assert not (target / "0.5+styx").exists()


def test_stdout_prints_one_version():
    result = runner.invoke(app, ["schema-export", "--stdout", "--version", "0.5+styx"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["properties"]["schema-version"]["const"] == "0.5+styx"


def test_stdout_requires_version():
    result = runner.invoke(app, ["schema-export", "--stdout"])
    assert result.exit_code != 0
    assert "--stdout requires --version" in result.stderr or "--stdout requires --version" in (
        result.output
    )


def test_unknown_version_errors():
    result = runner.invoke(app, ["schema-export", "--version", "9.9"])
    assert result.exit_code != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Unknown schema version" in combined
