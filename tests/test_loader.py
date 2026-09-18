import json
from pathlib import Path
from unittest.mock import patch

import pytest

from boutiques.loader import (
    DescriptorLoadError,
    _normalize_github_url,
    load_descriptor,
    load_invocation,
)
from boutiques.models.v05 import Descriptor as V05Descriptor

FIXTURES = Path(__file__).parent / "fixtures"


def test_load_from_path():
    descriptor = load_descriptor(FIXTURES / "v05" / "fsl_bet.json")
    assert isinstance(descriptor, V05Descriptor)


def test_load_from_str_path():
    descriptor = load_descriptor(str(FIXTURES / "v05" / "fsl_bet.json"))
    assert isinstance(descriptor, V05Descriptor)


def test_load_from_json_literal():
    raw = (FIXTURES / "v05" / "fsl_bet.json").read_text()
    descriptor = load_descriptor(raw)
    assert isinstance(descriptor, V05Descriptor)


def test_load_from_long_json_literal_does_not_filesystem_check():
    """Regression: long JSON strings used to trip OSError ENAMETOOLONG on Linux
    when ``read_data`` tried ``Path(source).exists()`` before parsing.
    """
    raw = (FIXTURES / "v05" / "fsl_bet.json").read_text()
    # Pad to ensure we're well past any OS path-length limit.
    padded = raw + " " * 5000
    descriptor = load_descriptor(padded)
    assert isinstance(descriptor, V05Descriptor)


def test_load_from_dict():
    raw = json.loads((FIXTURES / "v05" / "fsl_bet.json").read_text())
    descriptor = load_descriptor(raw)
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
        descriptor = load_descriptor("https://example.com/fsl_bet.json")
    assert isinstance(descriptor, V05Descriptor)
    urlopen_mock.assert_called_once()


def test_load_from_url_raises_on_network_failure():
    from urllib.error import URLError

    with patch("boutiques.loader.urlopen", side_effect=URLError("nope")):
        with pytest.raises(DescriptorLoadError, match="Failed to fetch"):
            load_descriptor("https://example.com/does-not-exist.json")


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


def test_load_invocation_from_path(tmp_path):
    inv = tmp_path / "inv.json"
    inv.write_text('{"x": "v"}')
    assert load_invocation(inv) == {"x": "v"}


def test_load_invocation_from_json_string():
    assert load_invocation('{"x": "v"}') == {"x": "v"}


def test_load_invocation_from_dict():
    assert load_invocation({"x": "v"}) == {"x": "v"}


def test_load_invocation_does_not_fetch_url():
    """Invocation loading never touches the network, even for http(s) sources."""
    with patch("boutiques.loader.urlopen") as urlopen_mock:
        with pytest.raises(ValueError):
            load_invocation("https://example.com/inv.json")
    urlopen_mock.assert_not_called()
