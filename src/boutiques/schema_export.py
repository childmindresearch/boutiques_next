"""Generate JSON Schema artifacts from the Pydantic models."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from boutiques.models.v05 import Descriptor as V05Descriptor
from boutiques.models.v05_styx import Descriptor as V05StyxDescriptor

VERSIONS: dict[str, type[BaseModel]] = {
    "0.5": V05Descriptor,
    "0.5+styx": V05StyxDescriptor,
}


def schema_for(version: str) -> dict[str, Any]:
    """Return the JSON Schema for a given Boutiques schema version."""
    try:
        model_cls = VERSIONS[version]
    except KeyError as exc:
        known = ", ".join(sorted(VERSIONS))
        raise KeyError(f"Unknown schema version {version!r}. Known: {known}.") from exc
    return model_cls.model_json_schema(by_alias=True)


def export_all(out_dir: Path) -> list[Path]:
    """Write ``descriptor.schema.json`` for every known version under ``out_dir``."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for version in VERSIONS:
        target_dir = out_dir / version
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / "descriptor.schema.json"
        target.write_text(json.dumps(schema_for(version), indent=2) + "\n")
        written.append(target)
    return written
