"""Soft advisories for descriptors that load successfully.

Lint covers the "recommended but not required" tier: a descriptor that
parses cleanly may still have stylistic or portability concerns. Each
``LintIssue`` is informational — it does not block validation or
execution.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

from boutiques._walk import walk_inputs, walk_scopes
from boutiques.loader import AnyDescriptor
from boutiques.models.v05_styx import Descriptor as V05StyxDescriptor

_VALUE_KEY_CONVENTION = re.compile(r"^\[[A-Z0-9_]+\]$")
_PATH_TEMPLATE_UNSAFE = re.compile(r'[<>:"\\|?*]')
_COMMAND_LINE_TOKEN = re.compile(r"\[([A-Z0-9_]+)\]")


@dataclass
class LintIssue:
    """A non-blocking advisory about a descriptor."""

    field: str
    message: str
    level: str = "warning"

    def __str__(self) -> str:
        if self.field:
            return f"[{self.level}] {self.field}: {self.message}"
        return f"[{self.level}] {self.message}"


# ---------------------------------------------------------------------------
# Top-level recommendations
# ---------------------------------------------------------------------------


def _recommend_tool_version(d: AnyDescriptor) -> list[LintIssue]:
    if isinstance(d, V05StyxDescriptor) and d.tool_version is None:
        return [
            LintIssue(
                field="tool-version",
                message=(
                    "Recommended: declare tool-version so the descriptor is "
                    "self-contained outside of any packaging metadata."
                ),
            )
        ]
    return []


def _recommend_container_image(d: AnyDescriptor) -> list[LintIssue]:
    if d.container_image is None:
        return [
            LintIssue(
                field="container-image",
                message=(
                    "Recommended: declare a container-image so the tool can be "
                    "launched reproducibly without external configuration."
                ),
            )
        ]
    return []


# ---------------------------------------------------------------------------
# Per-input / per-output / per-scope recommendations
# ---------------------------------------------------------------------------


def _recommend_value_key_format(d: AnyDescriptor) -> list[LintIssue]:
    """Convention: value-keys should match ``[UPPER_CASE]``."""
    issues: list[LintIssue] = []
    for path, inp in walk_inputs(d):
        vk = getattr(inp, "value_key", None)
        if vk and not _VALUE_KEY_CONVENTION.match(vk):
            issues.append(
                LintIssue(
                    field=f"{path}.value-key",
                    message=(
                        f"Convention: value-keys should match [UPPER_CASE], got {vk!r}."
                    ),
                )
            )
    return issues


def _recommend_safe_path_template_chars(d: AnyDescriptor) -> list[LintIssue]:
    """Flag path-templates containing characters Windows forbids in filenames."""
    issues: list[LintIssue] = []
    for scope_path, scope in walk_scopes(d):
        outputs = getattr(scope, "output_files", None) or []
        for i, output in enumerate(outputs):
            templates = [output.path_template] if output.path_template else []
            for entry in output.conditional_path_template or []:
                templates.extend(entry.values())
            for template in templates:
                if template and _PATH_TEMPLATE_UNSAFE.search(template):
                    prefix = f"{scope_path}." if scope_path else ""
                    issues.append(
                        LintIssue(
                            field=f"{prefix}output-files[{i}].path-template",
                            message=(
                                f"path-template {template!r} contains characters "
                                'unsafe on Windows filesystems (<>:"\\|?*).'
                            ),
                        )
                    )
    return issues


def _recommend_no_duplicate_command_tokens(d: AnyDescriptor) -> list[LintIssue]:
    """Same ``[KEY]`` appearing twice in one command-line is usually a bug.

    Substitution will replace every occurrence, so two literal copies
    of the same token will resolve to the same value at both positions.
    Rarely intentional.
    """
    issues: list[LintIssue] = []
    for scope_path, scope in walk_scopes(d):
        command_line = getattr(scope, "command_line", None) or ""
        counts = Counter(_COMMAND_LINE_TOKEN.findall(command_line))
        for token, n in counts.items():
            if n > 1:
                prefix = f"{scope_path}." if scope_path else ""
                issues.append(
                    LintIssue(
                        field=f"{prefix}command-line",
                        message=(
                            f"Token [{token}] appears {n} times in the command-line; "
                            "all occurrences resolve to the same value."
                        ),
                    )
                )
    return issues


_RECOMMENDATIONS: list[Callable[[AnyDescriptor], list[LintIssue]]] = [
    _recommend_tool_version,
    _recommend_container_image,
    _recommend_value_key_format,
    _recommend_safe_path_template_chars,
    _recommend_no_duplicate_command_tokens,
]


def lint(descriptor: AnyDescriptor) -> list[LintIssue]:
    """Return advisory issues for a successfully loaded descriptor."""
    issues: list[LintIssue] = []
    for check in _RECOMMENDATIONS:
        issues.extend(check(descriptor))
    return issues
