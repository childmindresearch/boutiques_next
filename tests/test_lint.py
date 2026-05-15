from pathlib import Path

import pytest

from boutiques.lint import lint
from boutiques.loader import load
from boutiques.models.v05_styx import FileInput
from boutiques.validate import validate

FIXTURES = Path(__file__).parent / "fixtures"
NIWRAP = FIXTURES / "v05_styx" / "niwrap_style.json"


def test_niwrap_style_descriptor_loads_under_v05_styx():
    """No tool-version, no container-image, uses styx FileInput extensions."""
    descriptor = load(NIWRAP)
    assert descriptor.schema_version == "0.5+styx"
    assert descriptor.tool_version is None
    assert descriptor.container_image is None
    # The FileInput is the v05_styx subclass that supports mutable / resolve-parent.
    file_input = descriptor.inputs[0]
    assert isinstance(file_input, FileInput)
    assert file_input.resolve_parent is True


def test_lint_flags_recommended_fields():
    descriptor = load(NIWRAP)
    issues = lint(descriptor)
    fields = {i.field for i in issues}
    assert "tool-version" in fields
    assert "container-image" in fields
    assert all(i.level == "warning" for i in issues)


def test_validate_returns_ok_with_warnings():
    result = validate(NIWRAP)
    assert result.ok
    assert result.warnings
    assert "OK with warnings" in result.format()


def test_v05_rejects_descriptor_without_tool_version(tmp_path):
    """v05 stays strict — flipping the schema-version makes the same file invalid."""
    import json

    raw = json.loads(NIWRAP.read_text())
    raw["schema-version"] = "0.5"
    # Strip the styx-only fields so v05 doesn't reject those first.
    raw["inputs"][0].pop("mutable", None)
    raw["inputs"][0].pop("resolve-parent", None)
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(raw))

    result = validate(bad)
    assert not result.ok
    assert any("tool-version" in str(e) for e in result.errors)


def test_lint_clean_when_all_recommended_present():
    """A complete descriptor produces no lint warnings."""
    complete = load(FIXTURES / "v05" / "fsl_bet.json")
    assert lint(complete) == []
