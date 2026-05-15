from pathlib import Path

import pytest

from boutiques.loader import DescriptorLoadError, load
from boutiques.models.v_0_5 import Descriptor as V05Descriptor
from boutiques.models.v_styx_1 import (
    Descriptor as VStyx1Descriptor,
    SubCommandUnionInput,
)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("path", sorted((FIXTURES / "v_0_5").glob("*.json")))
def test_v0_5_examples_round_trip(path):
    descriptor = load(path)
    assert isinstance(descriptor, V05Descriptor)
    assert descriptor.schema_version == "0.5"


def test_v_styx_1_subcommand_union():
    descriptor = load(FIXTURES / "v_styx_1" / "subcommand_union.json")
    assert isinstance(descriptor, VStyx1Descriptor)
    op = descriptor.inputs[0]
    assert isinstance(op, SubCommandUnionInput)
    assert [sc.id for sc in op.type] == ["blur", "sharpen"]


def test_unknown_schema_version_raises():
    with pytest.raises(DescriptorLoadError, match="Unknown or missing schema-version"):
        load({"schema-version": "0.99", "name": "x"})


def test_v0_5_strict_superset_loads_under_styx():
    # Any v0.5 descriptor, with only schema-version flipped, must load as v0.5+styx.
    fsl = load(FIXTURES / "v_0_5" / "fsl_bet.json")
    raw = fsl.model_dump(by_alias=True, exclude_none=True)
    raw["schema-version"] = "0.5+styx"
    upgraded = load(raw)
    assert isinstance(upgraded, VStyx1Descriptor)
    assert upgraded.name == fsl.name
    assert len(upgraded.inputs) == len(fsl.inputs)
