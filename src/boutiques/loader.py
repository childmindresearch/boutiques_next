"""Load descriptors from disk or dict, dispatching on ``schema-version``."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Union

from pydantic import ValidationError

from boutiques.models.v_0_5 import Descriptor as V05Descriptor
from boutiques.models.v_styx_1 import Descriptor as VStyx1Descriptor

AnyDescriptor = Union[V05Descriptor, VStyx1Descriptor]

_SCHEMA_MODELS: dict[str, type] = {
    "0.5": V05Descriptor,
    "0.5+styx": VStyx1Descriptor,
}


class DescriptorLoadError(Exception):
    """Raised when a descriptor cannot be parsed or its schema-version is unknown."""


def load(source: Union[str, Path, dict[str, Any]]) -> AnyDescriptor:
    """Load a descriptor from a file path, a JSON string, or a dict.

    The ``schema-version`` field selects the model. Unknown versions raise
    ``DescriptorLoadError``.
    """
    data = _read(source)
    version = data.get("schema-version")
    if version not in _SCHEMA_MODELS:
        known = ", ".join(sorted(_SCHEMA_MODELS))
        raise DescriptorLoadError(
            f"Unknown or missing schema-version {version!r}. Known versions: {known}."
        )
    model_cls = _SCHEMA_MODELS[version]
    try:
        return model_cls.model_validate(data)
    except ValidationError as exc:
        raise DescriptorLoadError(str(exc)) from exc


def _read(source: Union[str, Path, dict[str, Any]]) -> dict[str, Any]:
    if isinstance(source, dict):
        return source
    if isinstance(source, Path):
        return json.loads(source.read_text())
    # str: try a path first, then fall back to a JSON literal.
    as_path = Path(source)
    if as_path.exists():
        return json.loads(as_path.read_text())
    return json.loads(source)
