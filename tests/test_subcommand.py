from pathlib import Path

import pytest
from pydantic import ValidationError

from boutiques.example import generate
from boutiques.execution import resolve, simulate
from boutiques.invocation import invocation_model_for
from boutiques.invocation_check import validate_invocation
from boutiques.loader import load

FIXTURES = Path(__file__).parent / "fixtures"
SUBCMD = FIXTURES / "v05_styx" / "subcommand_union.json"


def _repeatable_verbose():
    """The issue's fmriprep-style descriptor: a `list: true` sub-command."""
    return load(
        {
            "schema-version": "0.5+styx",
            "name": "fmriprep",
            "description": "x",
            "command-line": "fmriprep [VERBOSE]",
            "inputs": [
                {
                    "id": "verbose",
                    "name": "verbose",
                    "description": "",
                    "value-key": "[VERBOSE]",
                    "list": True,
                    "min-list-entries": 0,
                    "type": {
                        "id": "verbose_token",
                        "name": "verbose_token",
                        "command-line": "--verbose",
                        "inputs": [],
                    },
                }
            ],
        }
    )


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


# ---- Repeatable (list: true) sub-commands --------------------------------


def test_list_subcommand_model_accepts_multiple_blocks():
    """`list: true` wraps the nested sub-command model in `list[...]`."""
    descriptor = _repeatable_verbose()
    model = invocation_model_for(descriptor)
    parsed = model.model_validate({"verbose": [{}, {}]})
    assert parsed.model_dump(by_alias=True)["verbose"] == [{}, {}]


def test_list_subcommand_model_rejects_single_dict():
    descriptor = _repeatable_verbose()
    model = invocation_model_for(descriptor)
    with pytest.raises(ValidationError):
        model.model_validate({"verbose": {}})


def test_list_subcommand_model_enforces_min_list_entries():
    descriptor = load(
        {
            "schema-version": "0.5+styx",
            "name": "t",
            "tool-version": "0.1",
            "description": "x",
            "command-line": "t [OP]",
            "inputs": [
                {
                    "id": "op",
                    "name": "OP",
                    "value-key": "[OP]",
                    "list": True,
                    "min-list-entries": 2,
                    "type": {"id": "do", "command-line": "do [X]", "inputs": []},
                }
            ],
        }
    )
    errs = validate_invocation(descriptor, {"op": [{}]})
    assert any("at least 2" in str(e) for e in errs)
    assert validate_invocation(descriptor, {"op": [{}, {}]}) == []


def test_simulate_repeats_subcommand_per_list_entry():
    descriptor = _repeatable_verbose()
    cmd = simulate(descriptor, {"verbose": [{}, {}]})
    assert cmd == "fmriprep --verbose --verbose"


def test_simulate_single_entry_and_empty_list():
    descriptor = _repeatable_verbose()
    assert simulate(descriptor, {"verbose": [{}]}) == "fmriprep --verbose"
    assert simulate(descriptor, {"verbose": []}) == "fmriprep"


def test_simulate_repeatable_transform_from_spec_docs():
    """docs/spec/subcommands.md: two transforms resolve back-to-back."""
    descriptor = load(
        {
            "schema-version": "0.5+styx",
            "name": "transformer",
            "tool-version": "1.0",
            "description": "x",
            "command-line": "apply [TRANSFORMS]",
            "inputs": [
                {
                    "id": "transformations",
                    "name": "T",
                    "value-key": "[TRANSFORMS]",
                    "list": True,
                    "optional": True,
                    "type": {
                        "id": "transform",
                        "command-line": "--transform [TYPE] [PARAMETERS]",
                        "inputs": [
                            {
                                "id": "type",
                                "name": "Type",
                                "type": "String",
                                "value-key": "[TYPE]",
                                "value-choices": ["rotate", "scale", "translate"],
                            },
                            {
                                "id": "parameters",
                                "name": "P",
                                "type": "Number",
                                "list": True,
                                "value-key": "[PARAMETERS]",
                            },
                        ],
                    },
                }
            ],
        }
    )
    inv = {
        "transformations": [
            {"type": "rotate", "parameters": [0, 0, 90]},
            {"type": "scale", "parameters": [2, 2, 1]},
        ]
    }
    assert simulate(descriptor, inv) == (
        "apply --transform rotate 0.0 0.0 90.0 --transform scale 2.0 2.0 1.0"
    )


def test_simulate_union_list_with_mixed_types():
    descriptor = load(
        {
            "schema-version": "0.5+styx",
            "name": "m",
            "tool-version": "0.1",
            "description": "x",
            "command-line": "m [OP] [VOL]",
            "inputs": [
                {
                    "id": "op",
                    "name": "OP",
                    "value-key": "[OP]",
                    "list": True,
                    "optional": True,
                    "type": [
                        {
                            "id": "blur",
                            "command-line": "blur [SIGMA]",
                            "inputs": [
                                {
                                    "id": "sigma",
                                    "name": "S",
                                    "type": "Number",
                                    "value-key": "[SIGMA]",
                                }
                            ],
                        },
                        {
                            "id": "sharpen",
                            "command-line": "sharpen [AMT]",
                            "inputs": [
                                {
                                    "id": "amt",
                                    "name": "A",
                                    "type": "Number",
                                    "value-key": "[AMT]",
                                }
                            ],
                        },
                    ],
                },
                {"id": "vol", "name": "V", "type": "File", "value-key": "[VOL]"},
            ],
        }
    )
    inv = {
        "op": [
            {"@type": "blur", "sigma": 1.5},
            {"@type": "sharpen", "amt": 0.7},
        ],
        "vol": "/in.nii",
    }
    assert resolve(descriptor, inv) == ["m", "blur", "1.5", "sharpen", "0.7", "/in.nii"]


def test_example_generates_a_list_for_repeatable_subcommand():
    descriptor = _repeatable_verbose()
    assert generate(descriptor) == {"verbose": [{}]}


def test_example_repeats_to_min_list_entries():
    descriptor = load(
        {
            "schema-version": "0.5+styx",
            "name": "t",
            "tool-version": "0.1",
            "description": "x",
            "command-line": "t [OP]",
            "inputs": [
                {
                    "id": "op",
                    "name": "OP",
                    "value-key": "[OP]",
                    "list": True,
                    "min-list-entries": 2,
                    "type": {
                        "id": "do",
                        "command-line": "do --flag",
                        "inputs": [],
                    },
                }
            ],
        }
    )
    assert generate(descriptor) == {"op": [{}, {}]}
