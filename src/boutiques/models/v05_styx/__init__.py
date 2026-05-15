"""Boutiques 0.5+styx descriptor model (strict superset of 0.5)."""

from boutiques.models.v05_styx.descriptor import Descriptor
from boutiques.models.v05_styx.inputs import (
    FileInput,
    FlagInput,
    Input,
    NumberInput,
    StringInput,
    SubCommandInput,
    SubCommandType,
    SubCommandUnionInput,
)
from boutiques.models.v05_styx.stdio_outputs import StderrOutput, StdoutOutput

__all__ = [
    "Descriptor",
    "FileInput",
    "FlagInput",
    "Input",
    "NumberInput",
    "StderrOutput",
    "StdoutOutput",
    "StringInput",
    "SubCommandInput",
    "SubCommandType",
    "SubCommandUnionInput",
]
