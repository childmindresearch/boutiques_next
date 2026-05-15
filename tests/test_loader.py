import json
from pathlib import Path
from unittest.mock import patch

import pytest

from boutiques.loader import DescriptorLoadError, _normalize_github_url, load
from boutiques.models.v05 import Descriptor as V05Descriptor

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_from_path():
    descriptor = load(FIXTURES / "v05" / "fsl_bet.json")
    assert isinstance(descriptor, V05Descriptor)


def test_load_from_str_path():
    descriptor = load(str(FIXTURES / "v05" / "fsl_bet.json"))
    assert isinstance(descriptor, V05Descriptor)


def test_load_from_json_literal():
    raw = (FIXTURES / "v05" / "fsl_bet.json").read_text()
    descriptor = load(raw)
    assert isinstance(descriptor, V05Descriptor)


def test_load_from_dict():
    raw = json.loads((FIXTURES / "v05" / "fsl_bet.json").read_text())
    descriptor = load(raw)
    assert isinstance(descriptor, V05Descriptor)


def test_load_from_url_uses_urllib():
    """URL loading hits urlopen; mock it so the test stays offline."""
    raw = (FIXTURES / "v05" / "fsl_bet.json").read_bytes()

    class _Response:
        def read(self):
            return raw

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    with patch("boutiques.loader.urlopen", return_value=_Response()) as urlopen_mock:
        descriptor = load("https://example.com/fsl_bet.json")
    assert isinstance(descriptor, V05Descriptor)
    urlopen_mock.assert_called_once()


def test_load_from_url_raises_on_network_failure():
    from urllib.error import URLError

    with patch("boutiques.loader.urlopen", side_effect=URLError("nope")):
        with pytest.raises(DescriptorLoadError, match="Failed to fetch"):
            load("https://example.com/does-not-exist.json")


def test_github_blob_url_rewrites_to_raw():
    blob = "https://github.com/boutiques/boutiques/blob/main/example.json"
    assert _normalize_github_url(blob) == (
        "https://raw.githubusercontent.com/boutiques/boutiques/main/example.json"
    )


def test_github_blob_url_with_subpath():
    blob = (
        "https://github.com/boutiques/boutiques/blob/master/"
        "boutiques/schema/examples/fsl_bet/fsl_bet.json"
    )
    assert _normalize_github_url(blob).startswith("https://raw.githubusercontent.com/")
    assert blob.endswith("fsl_bet.json")


def test_raw_url_passthrough():
    raw = "https://raw.githubusercontent.com/boutiques/boutiques/main/x.json"
    assert _normalize_github_url(raw) == raw
