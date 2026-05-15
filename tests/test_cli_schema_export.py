"""Tests for ``bosh schema-export``."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from boutiques.cli import app
from boutiques.schema_export import VERSIONS

runner = CliRunner()


def test_no_output_prints_default_version_to_stdout():
    """Without -o or --version: print the 0.5+styx schema to stdout."""
    result = runner.invoke(app, ["schema-export"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["properties"]["schema-version"]["const"] == "0.5+styx"


def test_no_output_with_version_prints_to_stdout():
    result = runner.invoke(app, ["schema-export", "--version", "0.5"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["properties"]["schema-version"]["const"] == "0.5"


def test_output_writes_both_versions(tmp_path):
    target = tmp_path / "schema"
    result = runner.invoke(app, ["schema-export", "--output", str(target)])
    assert result.exit_code == 0
    for version in VERSIONS:
        path = target / version / "descriptor.schema.json"
        assert path.exists()
        schema = json.loads(path.read_text())
        assert "properties" in schema
        assert "name" in schema["properties"]
        assert f"Wrote {path}" in result.stdout


def test_output_with_version_writes_one_file(tmp_path):
    target = tmp_path / "schema"
    result = runner.invoke(app, ["schema-export", "--output", str(target), "--version", "0.5"])
    assert result.exit_code == 0
    assert (target / "0.5" / "descriptor.schema.json").exists()
    assert not (target / "0.5+styx").exists()


def test_unknown_version_errors():
    result = runner.invoke(app, ["schema-export", "--version", "9.9"])
    assert result.exit_code != 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Unknown schema version" in combined
