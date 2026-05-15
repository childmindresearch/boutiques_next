from pathlib import Path

import pytest
from pydantic import ValidationError

from boutiques.example import generate
from boutiques.execution import simulate
from boutiques.invocation import invocation_model_for
from boutiques.loader import load

FIXTURES = Path(__file__).parent / "fixtures"
SUBCMD = FIXTURES / "v05_styx" / "subcommand_union.json"


def test_invocation_model_builds_for_subcommand_union():
    descriptor = load(SUBCMD)
    model = invocation_model_for(descriptor)
    # Discriminated union by '@type' (Styx convention) inside the 'op' input.
    inv = {
        "op": {"@type": "blur", "sigma": 1.5},
        "volumes": ["/data/in.nii"],
    }
    parsed = model.model_validate(inv)
    assert parsed.op.type_ == "blur"
    assert parsed.op.sigma == 1.5


def test_invocation_model_rejects_unknown_subcommand_id():
    descriptor = load(SUBCMD)
    model = invocation_model_for(descriptor)
    with pytest.raises(ValidationError):
        model.model_validate({"op": {"@type": "nonexistent", "amount": 0.5}, "volumes": ["/v.nii"]})


def test_simulate_resolves_chosen_subcommand():
    descriptor = load(SUBCMD)
    cmd = simulate(
        descriptor,
        {"op": {"@type": "sharpen", "amount": 0.7}, "volumes": ["/data/v1.nii", "/data/v2.nii"]},
    )
    assert cmd == "mri sharpen 0.7 /data/v1.nii /data/v2.nii"


def test_simulate_resolves_other_subcommand():
    descriptor = load(SUBCMD)
    cmd = simulate(
        descriptor,
        {"op": {"@type": "blur", "sigma": 2.0}, "volumes": ["/in.nii"]},
    )
    assert cmd == "mri blur 2.0 /in.nii"


def test_example_picks_first_subcommand_with_type_tag():
    descriptor = load(SUBCMD)
    inv = generate(descriptor)
    assert inv["op"]["@type"] == "blur"
    # @type is the required discriminator for the union.
    assert "@type" in inv["op"]


def test_example_roundtrips_through_simulate():
    descriptor = load(SUBCMD)
    inv = generate(descriptor)
    cmd = simulate(descriptor, inv)
    # Whichever sub-command was chosen, the resolved command-line should
    # mention it by name in the parent's command-line template.
    chosen_id = inv["op"]["@type"]
    assert chosen_id in cmd


def test_id_style_invocation_is_rejected():
    """Sanity check: pre-flip ``id``-based invocations no longer validate."""
    descriptor = load(SUBCMD)
    model = invocation_model_for(descriptor)
    with pytest.raises(ValidationError):
        model.model_validate({"op": {"id": "blur", "sigma": 1.5}, "volumes": ["/v.nii"]})
