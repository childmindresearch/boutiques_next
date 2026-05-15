"""Inputs whose ids would shadow BaseModel attributes must not warn."""

from __future__ import annotations

import warnings

import pytest

from boutiques.execution import simulate
from boutiques.invocation import invocation_model_for
from boutiques.loader import load


def _descriptor_with_id(input_id: str):
    return load(
        {
            "schema-version": "0.5",
            "name": "t",
            "description": "x",
            "tool-version": "1.0",
            "command-line": f"tool [{input_id.upper()}]",
            "inputs": [
                {
                    "id": input_id,
                    "name": input_id,
                    "type": "String",
                    "value-key": f"[{input_id.upper()}]",
                }
            ],
        }
    )


@pytest.mark.parametrize("input_id", ["register", "copy", "json", "dict", "schema", "validate"])
def test_shadowing_input_id_emits_no_warning(input_id):
    descriptor = _descriptor_with_id(input_id)
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        invocation_model_for(descriptor)  # would raise if Pydantic warned


def test_shadowing_input_id_still_loads_invocation_by_alias():
    """The JSON alias is preserved; users still pass ``register`` as the key."""
    descriptor = _descriptor_with_id("register")
    model = invocation_model_for(descriptor)
    parsed = model.model_validate({"register": "value"})
    # Internal Pydantic field name is mangled, alias is the original
    assert parsed.model_dump(by_alias=True) == {"register": "value"}


def test_shadowing_input_id_resolves_correctly():
    """End-to-end: simulate substitutes the value via the original value-key."""
    descriptor = _descriptor_with_id("register")
    assert simulate(descriptor, {"register": "foo"}) == "tool foo"
