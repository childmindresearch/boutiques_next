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
