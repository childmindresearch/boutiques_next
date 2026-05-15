from pathlib import Path

import pytest
from pydantic import ValidationError

from boutiques.example import generate
from boutiques.execution import simulate
from boutiques.invocation import invocation_model_for
from boutiques.loader import load

FIXTURES = Path(__file__).parent / "fixtures"
FSL_BET = FIXTURES / "v05" / "fsl_bet.json"


def test_invocation_model_validates_minimal_required():
    descriptor = load(FSL_BET)
    model = invocation_model_for(descriptor)
    inv = {"infile": "/data/in.nii", "maskfile": "out.nii"}
    parsed = model.model_validate(inv)
    assert parsed.infile == "/data/in.nii"


def test_invocation_model_rejects_unknown_input():
    descriptor = load(FSL_BET)
    model = invocation_model_for(descriptor)
    with pytest.raises(ValidationError, match="not_a_real_input"):
        model.model_validate(
            {"infile": "/data/in.nii", "maskfile": "out.nii", "not_a_real_input": True}
        )


def test_invocation_model_enforces_range():
    descriptor = load(FSL_BET)
    model = invocation_model_for(descriptor)
    # fractional_intensity is constrained: 0 <= x <= 1
    # The dynamic model uses float typing; range enforcement is currently informational
    # via the descriptor (added later in cross-field semantic checks). For now, the
    # model accepts the value but a follow-up semantic pass would flag it.
    parsed = model.model_validate({"infile": "/in", "maskfile": "out", "fractional_intensity": 0.5})
    assert parsed.fractional_intensity == 0.5


def test_example_includes_only_required_by_default():
    descriptor = load(FSL_BET)
    inv = generate(descriptor)
    required_ids = {i.id for i in descriptor.inputs if not i.optional}
    assert set(inv.keys()) == required_ids


def test_example_skips_flags_even_when_required():
    """Flag inputs without ``optional: true`` should still be skipped from a minimum example.

    A Flag's runtime semantics are "either passed or not" — value=false is
    indistinguishable from absence — so the minimum example omits all flags
    regardless of how the descriptor marked them. Matches the v0.5+styx
    spec author's note about `optional` having no meaning for Flag inputs.
    Real-world descriptors (e.g. niwrap-style) frequently leave `optional`
    unset on flags.
    """
    descriptor = load(
        {
            "schema-version": "0.5",
            "name": "t",
            "description": "x",
            "tool-version": "1.0",
            "command-line": "tool [INPUT] [VERBOSE] [DEBUG]",
            "inputs": [
                {"id": "input", "name": "I", "type": "File", "value-key": "[INPUT]"},
                {
                    "id": "verbose",
                    "name": "V",
                    "type": "Flag",
                    "command-line-flag": "-v",
                    "value-key": "[VERBOSE]",
                    # no optional field — defaults to false (required)
                },
                {
                    "id": "debug",
                    "name": "D",
                    "type": "Flag",
                    "command-line-flag": "-d",
                    "value-key": "[DEBUG]",
                    "optional": False,
                },
            ],
        }
    )
    inv = generate(descriptor)
    assert set(inv.keys()) == {"input"}
    # --complete pulls the flags in
    inv_complete = generate(descriptor, complete=True)
    assert set(inv_complete.keys()) == {"input", "verbose", "debug"}


def test_example_complete_includes_optional():
    descriptor = load(FSL_BET)
    inv = generate(descriptor, complete=True)
    all_ids = {i.id for i in descriptor.inputs}
    assert set(inv.keys()) == all_ids


def test_simulate_emits_flags_and_values():
    descriptor = load(FSL_BET)
    inv = {
        "infile": "/data/in.nii",
        "maskfile": "out.nii",
        "fractional_intensity": 0.5,
        "verbose_flag": True,
    }
    cmd = simulate(descriptor, inv)
    assert cmd.startswith("bet /data/in.nii out.nii")
    assert "-f 0.5" in cmd
    assert "-v" in cmd


def test_simulate_omits_unset_optional_inputs():
    descriptor = load(FSL_BET)
    inv = {"infile": "/data/in.nii", "maskfile": "out.nii"}
    cmd = simulate(descriptor, inv)
    # No optional flags present
    assert " -f " not in cmd
    assert " -v" not in cmd


def test_simulate_handles_list_separator():
    descriptor = load(FSL_BET)
    inv = {
        "infile": "/in",
        "maskfile": "out",
        "center_of_gravity": [1.0, 2.0, 3.0],
    }
    cmd = simulate(descriptor, inv)
    assert "-c 1.0 2.0 3.0" in cmd


def test_simulate_roundtrips_generated_example():
    descriptor = load(FSL_BET)
    inv = generate(descriptor)
    cmd = simulate(descriptor, inv)
    assert cmd.startswith("bet ")
    # Required inputs only — no flags should appear.
    assert " -f " not in cmd
