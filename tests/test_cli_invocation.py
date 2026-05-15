"""Tests for ``bosh invocation`` (validator) and ``bosh invocation-schema`` (dumper)."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from boutiques.cli import app
from boutiques.invocation import invocation_schema
from boutiques.loader import load

FIXTURES = Path(__file__).parent / "fixtures"
runner = CliRunner()


# ---- library: invocation_schema -----------------------------------------


def test_library_invocation_schema_for_simple_descriptor():
    descriptor = load(FIXTURES / "v05" / "fsl_bet.json")
    schema = invocation_schema(descriptor)
    assert schema["additionalProperties"] is False
    assert schema["properties"]["infile"]["type"] == "string"
    assert "infile" in schema["required"]
    fi = schema["properties"]["fractional_intensity"]
    assert any("null" in branch.get("type", "") for branch in fi["anyOf"])
    numeric_branch = next(b for b in fi["anyOf"] if b.get("type") == "number")
    assert numeric_branch["minimum"] == 0.0
    assert numeric_branch["maximum"] == 1.0


def test_library_invocation_schema_subcommand_union_uses_oneof():
    descriptor = load(FIXTURES / "v05_styx" / "subcommand_union.json")
    schema = invocation_schema(descriptor)
    op = schema["properties"]["op"]
    assert "oneOf" in op or "discriminator" in op
    defs = schema.get("$defs", {})
    assert any("blur" in name.lower() for name in defs)
    assert any("sharpen" in name.lower() for name in defs)


# ---- bosh invocation-schema (the dumper) --------------------------------


def test_invocation_schema_cli_prints_to_stdout():
    result = runner.invoke(
        app, ["invocation-schema", str(FIXTURES / "v05" / "fsl_bet.json")]
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "infile" in payload["properties"]


def test_invocation_schema_cli_writes_to_file(tmp_path):
    target = tmp_path / "out.json"
    result = runner.invoke(
        app,
        [
            "invocation-schema",
            str(FIXTURES / "v05" / "fsl_bet.json"),
            "-o",
            str(target),
        ],
    )
    assert result.exit_code == 0
    assert target.exists()
    payload = json.loads(target.read_text())
    assert "infile" in payload["properties"]


# ---- bosh invocation (the drop-in validator) ----------------------------


def test_invocation_plain_mode_confirms_schema_builds():
    """No flags: confirm the schema can be generated."""
    result = runner.invoke(
        app, ["invocation", str(FIXTURES / "v05" / "fsl_bet.json")]
    )
    assert result.exit_code == 0
    assert "OK" in result.stdout


def test_invocation_validates_valid_invocation(tmp_path):
    inv = tmp_path / "inv.json"
    inv.write_text(json.dumps({"infile": "/data/in.nii", "maskfile": "out.nii"}))
    result = runner.invoke(
        app,
        ["invocation", str(FIXTURES / "v05" / "fsl_bet.json"), "-i", str(inv)],
    )
    assert result.exit_code == 0
    assert "OK" in result.stdout


def test_invocation_rejects_invalid_invocation(tmp_path):
    inv = tmp_path / "inv.json"
    inv.write_text(
        json.dumps(
            {
                "infile": "/data/in.nii",
                "maskfile": "out.nii",
                "fractional_intensity": 5.0,  # max is 1
            }
        )
    )
    result = runner.invoke(
        app,
        ["invocation", str(FIXTURES / "v05" / "fsl_bet.json"), "-i", str(inv)],
    )
    assert result.exit_code == 1
    combined = (result.stdout or "") + (result.stderr or "")
    assert "less than or equal to" in combined
    assert "Traceback" not in combined


def test_invocation_write_schema_embeds_into_descriptor(tmp_path):
    """-w mutates the descriptor file in place, embedding the schema."""
    descriptor_copy = tmp_path / "descriptor.json"
    shutil.copy(FIXTURES / "v05" / "fsl_bet.json", descriptor_copy)
    assert "invocation-schema" not in json.loads(descriptor_copy.read_text())

    result = runner.invoke(app, ["invocation", str(descriptor_copy), "-w"])
    assert result.exit_code == 0
    assert "Wrote invocation-schema" in result.stdout

    updated = json.loads(descriptor_copy.read_text())
    assert "invocation-schema" in updated
    assert "properties" in updated["invocation-schema"]
    # Descriptor still loads under our model after the embed.
    re_loaded = load(descriptor_copy)
    assert re_loaded.name == "fsl_bet"


def test_invocation_write_schema_rejects_url():
    """-w only makes sense for local descriptors; reject http(s) URLs."""
    result = runner.invoke(
        app, ["invocation", "https://example.com/x.json", "-w"]
    )
    assert result.exit_code == 1
