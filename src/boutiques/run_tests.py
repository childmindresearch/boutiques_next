"""Run the test cases embedded in a descriptor's ``tests`` field.

Each test case carries an invocation and a set of assertions. The
runner launches the tool with the invocation, then checks the
assertions:

- ``exit-code``: compare the actual exit code against the expected.
- ``output-files``: for each declared output, verify the file exists at
  the resolved path. If the assertion includes ``md5-reference``,
  hash the file and compare.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path

from boutiques.execution import launch
from boutiques.execution.runtime.base import RuntimeError_
from boutiques.invocation_check import InvocationValidationError
from boutiques.loader import AnyDescriptor


@dataclass
class TestCaseResult:
    """Outcome of running one test case."""

    name: str
    exit_code: int
    duration_seconds: float
    failures: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.failures


@dataclass
class TestRunResults:
    """Outcome of running every test case in a descriptor."""

    descriptor_name: str
    cases: list[TestCaseResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.passed for c in self.cases)

    @property
    def num_passed(self) -> int:
        return sum(1 for c in self.cases if c.passed)

    @property
    def num_failed(self) -> int:
        return sum(1 for c in self.cases if not c.passed)


def run_tests(
    descriptor: AnyDescriptor,
    *,
    runtime: str = "local",
    cwd: Path | None = None,
) -> TestRunResults:
    """Run every test case declared on ``descriptor``."""
    results = TestRunResults(descriptor_name=descriptor.name)
    for case in descriptor.tests or []:
        results.cases.append(_run_one(descriptor, case, runtime=runtime, cwd=cwd))
    return results


def _run_one(
    descriptor: AnyDescriptor,
    case: object,
    *,
    runtime: str,
    cwd: Path | None,
) -> TestCaseResult:
    start = time.monotonic()
    try:
        launch_result = launch(
            descriptor,
            case.invocation,  # type: ignore[attr-defined]
            runtime=runtime,
            cwd=cwd,
            stream=False,
        )
    except InvocationValidationError as exc:
        return TestCaseResult(
            name=case.name,  # type: ignore[attr-defined]
            exit_code=-1,
            duration_seconds=time.monotonic() - start,
            failures=[f"invocation invalid: {line}" for line in str(exc).splitlines()],
        )
    except RuntimeError_ as exc:
        return TestCaseResult(
            name=case.name,  # type: ignore[attr-defined]
            exit_code=-1,
            duration_seconds=time.monotonic() - start,
            failures=[f"runtime error: {exc}"],
        )
    duration = time.monotonic() - start

    failures: list[str] = []
    assertions = case.assertions  # type: ignore[attr-defined]

    if assertions.exit_code is not None and launch_result.exit_code != assertions.exit_code:
        failures.append(
            f"exit-code: expected {assertions.exit_code}, got {launch_result.exit_code}"
        )

    for output_assertion in assertions.output_files or []:
        failures.extend(_check_output(output_assertion, launch_result))

    return TestCaseResult(
        name=case.name,  # type: ignore[attr-defined]
        exit_code=launch_result.exit_code,
        duration_seconds=duration,
        failures=failures,
    )


def _check_output(assertion: object, launch_result: object) -> list[str]:
    expected_id = assertion.id  # type: ignore[attr-defined]
    outputs = launch_result.outputs  # type: ignore[attr-defined]
    output = next((o for o in outputs if o.id == expected_id), None)
    if output is None:
        return [f"output-files: {expected_id!r} is not a declared output of this descriptor"]
    if output.path is None:
        # stdout-/stderr-output assertion: only the existence + md5 of files
        # is checkable. stdio outputs are caught by exit-code instead.
        return [f"output-files: {expected_id!r} is a stdio output; md5 checks not supported"]
    if not output.exists:
        return [f"output-files: {expected_id!r} expected at {output.path} but is missing"]

    reference = assertion.md5_reference  # type: ignore[attr-defined]
    if reference is None:
        return []  # existence alone was the only check
    actual = _md5(output.path)
    if actual != reference:
        return [f"output-files: {expected_id!r} md5 mismatch: expected {reference}, got {actual}"]
    return []


def _md5(path: Path) -> str:
    h = hashlib.md5()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


__all__ = ["TestCaseResult", "TestRunResults", "run_tests"]
