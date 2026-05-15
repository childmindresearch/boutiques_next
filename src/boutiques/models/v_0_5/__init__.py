"""Boutiques 0.5 descriptor model."""

from boutiques.models.v_0_5.containers import ContainerImage
from boutiques.models.v_0_5.descriptor import Descriptor
from boutiques.models.v_0_5.environment import EnvironmentVariable
from boutiques.models.v_0_5.errors import ErrorCode
from boutiques.models.v_0_5.groups import Group
from boutiques.models.v_0_5.inputs import FileInput, FlagInput, Input, NumberInput, StringInput
from boutiques.models.v_0_5.outputs import Output
from boutiques.models.v_0_5.resources import SuggestedResources
from boutiques.models.v_0_5.tests import TestCase

__all__ = [
    "ContainerImage",
    "Descriptor",
    "EnvironmentVariable",
    "ErrorCode",
    "FileInput",
    "FlagInput",
    "Group",
    "Input",
    "NumberInput",
    "Output",
    "StringInput",
    "SuggestedResources",
    "TestCase",
]
