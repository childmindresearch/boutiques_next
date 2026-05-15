"""Boutiques 0.5+styx descriptor model (strict superset of 0.5)."""

from boutiques.models.v_styx_1.descriptor import Descriptor
from boutiques.models.v_styx_1.inputs import (
    FileInput,
    FlagInput,
    Input,
    NumberInput,
    StringInput,
    SubCommandInput,
    SubCommandType,
    SubCommandUnionInput,
)

__all__ = [
    "Descriptor",
    "FileInput",
    "FlagInput",
    "Input",
    "NumberInput",
    "StringInput",
    "SubCommandInput",
    "SubCommandType",
    "SubCommandUnionInput",
]
