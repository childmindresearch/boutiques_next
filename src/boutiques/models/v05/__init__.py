"""Boutiques 0.5 descriptor model."""

from boutiques.models.v05.containers import ContainerImage
from boutiques.models.v05.descriptor import Descriptor
from boutiques.models.v05.environment import EnvironmentVariable
from boutiques.models.v05.errors import ErrorCode
from boutiques.models.v05.groups import Group
from boutiques.models.v05.inputs import FileInput, FlagInput, Input, NumberInput, StringInput
from boutiques.models.v05.outputs import Output
from boutiques.models.v05.resources import SuggestedResources
from boutiques.models.v05.tests import TestCase

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
