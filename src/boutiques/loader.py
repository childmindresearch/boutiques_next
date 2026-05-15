"""Load descriptors from disk, URL, dict, or JSON string.

The loader dispatches on ``schema-version`` and accepts four input forms:

- ``dict`` — already-parsed JSON
- ``Path`` — file on disk
- ``str`` — tried in order: existing path on disk, http(s) URL, raw JSON

URLs use the standard library (``urllib.request``) — no extra deps. The
loader auto-rewrites GitHub blob URLs to their raw equivalents so users
can paste links straight from the browser.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Union
from urllib.error import URLError
from urllib.request import Request, urlopen

from pydantic import ValidationError

from boutiques.models.v05 import Descriptor as V05Descriptor
from boutiques.models.v05_styx import Descriptor as V05StyxDescriptor

AnyDescriptor = Union[V05Descriptor, V05StyxDescriptor]

_SCHEMA_MODELS: dict[str, type] = {
    "0.5": V05Descriptor,
    "0.5+styx": V05StyxDescriptor,
}

_FETCH_TIMEOUT_SECONDS = 10
_GITHUB_BLOB_RE = re.compile(
    r"^https?://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/blob/(?P<ref>[^/]+)/(?P<path>.+)$"
)


class DescriptorLoadError(Exception):
    """Raised when a descriptor cannot be parsed or its schema-version is unknown."""


def load(source: Union[str, Path, dict[str, Any]]) -> AnyDescriptor:
    """Load a descriptor from a file path, URL, dict, or JSON string.

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
    # str: try a path first, then a URL, then a JSON literal.
    as_path = Path(source)
    if as_path.exists():
        return json.loads(as_path.read_text())
    if _looks_like_url(source):
        return _fetch_url(source)
    return json.loads(source)


def _looks_like_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def _fetch_url(url: str) -> dict[str, Any]:
    url = _normalize_github_url(url)
    request = Request(url, headers={"User-Agent": "boutiques-cli"})
    try:
        with urlopen(request, timeout=_FETCH_TIMEOUT_SECONDS) as response:
            payload = response.read().decode("utf-8")
    except URLError as exc:
        raise DescriptorLoadError(f"Failed to fetch {url}: {exc.reason}") from exc
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise DescriptorLoadError(
            f"Response from {url} is not valid JSON: {exc.msg}"
        ) from exc


def _normalize_github_url(url: str) -> str:
    """Convert ``github.com/.../blob/...`` URLs to their raw equivalents.

    Browser URLs return HTML, not the file content. We rewrite to
    ``raw.githubusercontent.com`` so users can paste links directly.
    """
    match = _GITHUB_BLOB_RE.match(url)
    if not match:
        return url
    g = match.groupdict()
    return f"https://raw.githubusercontent.com/{g['owner']}/{g['repo']}/{g['ref']}/{g['path']}"
