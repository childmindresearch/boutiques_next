"""Tests for ``bosh invocation`` and ``boutiques.invocation.invocation_schema``."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from boutiques.cli import app
from boutiques.invocation import invocation_schema
from boutiques.loader import load

FIXTURES = Path(__file__).parent / "fixtures"
runner = CliRunner()


def test_library_invocation_schema_for_simple_descriptor():
    descriptor = load(FIXTURES / "v05" / "fsl_bet.json")
    schema = invocation_schema(descriptor)
    assert schema["additionalProperties"] is False
    # Required inputs appear with no `null` in their type
    assert schema["properties"]["infile"]["type"] == "string"
    assert "infile" in schema["required"]
    # Optional inputs use the anyOf-with-null pattern Pydantic emits
    fi = schema["properties"]["fractional_intensity"]
    assert any("null" in branch.get("type", "") for branch in fi["anyOf"])
    # Numeric range surfaces as minimum/maximum
    numeric_branch = next(b for b in fi["anyOf"] if b.get("type") == "number")
    assert numeric_branch["minimum"] == 0.0
    assert numeric_branch["maximum"] == 1.0


def test_library_invocation_schema_subcommand_union_uses_oneof():
    descriptor = load(FIXTURES / "v05_styx" / "subcommand_union.json")
    schema = invocation_schema(descriptor)
    op = schema["properties"]["op"]
    # Discriminated union → oneOf with $defs references
    assert "oneOf" in op or "discriminator" in op
    # Both candidate models live under $defs
    defs = schema.get("$defs", {})
    assert any("blur" in name.lower() for name in defs)
    assert any("sharpen" in name.lower() for name in defs)


def test_cli_invocation_prints_to_stdout():
    result = runner.invoke(
        app, ["invocation", str(FIXTURES / "v05" / "fsl_bet.json")]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "infile" in payload["properties"]


def test_cli_invocation_writes_to_file(tmp_path):
    target = tmp_path / "out.json"
    result = runner.invoke(
        app,
        [
            "invocation",
            str(FIXTURES / "v05" / "fsl_bet.json"),
            "-o",
            str(target),
        ],
    )
    assert result.exit_code == 0
    assert target.exists()
    payload = json.loads(target.read_text())
    assert "infile" in payload["properties"]


def test_cli_invocation_rejects_unknown_descriptor():
    result = runner.invoke(app, ["invocation", "/no/such/path.json"])
    assert result.exit_code == 1
