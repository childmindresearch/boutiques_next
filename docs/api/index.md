# Python API

Every `bosh` subcommand delegates to a Python function in the same
package, so the CLI is reproducible from Python in two or three lines.
This page is auto-generated from the docstrings — if anything reads
oddly, it's a hint to improve the docstring in source.

## Quick reference

| Task | Function |
| --- | --- |
| Parse a descriptor (path / URL / dict / JSON) | [`load`](#boutiques.loader.load) |
| Validate (structural + semantic + lint) | [`validate`](#boutiques.validate.validate) |
| Generate a sample invocation | [`generate`](#boutiques.example.generate) |
| Resolve to argv | [`resolve`](#boutiques.execution.resolve.resolve) |
| Shell-safe display string | [`simulate`](#boutiques.execution.simulate) |
| Run the tool | [`launch`](#boutiques.execution.launch.launch) |
| Run descriptor `tests` | [`run_tests`](#boutiques.run_tests.run_tests) |
| Tree view | [`pprint`](#boutiques.prettyprint.pprint) |
| JSON Schema artifacts | [`export_all`](#boutiques.schema_export.export_all) |

---

## Loading

::: boutiques.loader.load
::: boutiques.loader.DescriptorLoadError

## Validation

### Top-level

::: boutiques.validate.validate
::: boutiques.validate.ValidationResult
::: boutiques.validate.ValidationError

### Lint advisories

::: boutiques.lint.lint
::: boutiques.lint.LintIssue

### Cross-field semantic checks

::: boutiques.semantic.check

## Example generation

::: boutiques.example.generate

## Execution

::: boutiques.execution.resolve.resolve
::: boutiques.execution.simulate
::: boutiques.execution.launch.launch
::: boutiques.execution.launch.LaunchResult
::: boutiques.execution.outputs.ResolvedOutput
::: boutiques.execution.outputs.resolve_output_paths
::: boutiques.execution.outputs.resolve_stdio_outputs
::: boutiques.execution.mounts.collect_file_mounts
::: boutiques.execution.runtime.base.RunResult
::: boutiques.execution.runtime.base.RuntimeError_

## Invocation model

::: boutiques.invocation.invocation_model_for
::: boutiques.invocation.InvocationModelError
::: boutiques.invocation_check.validate_invocation
::: boutiques.invocation_check.InvocationValidationError

## Test runner

::: boutiques.run_tests.run_tests
::: boutiques.run_tests.TestRunResults
::: boutiques.run_tests.TestCaseResult

## Pretty-printing

::: boutiques.prettyprint.pprint
::: boutiques.prettyprint.build_tree

## JSON Schema export

::: boutiques.schema_export.schema_for
::: boutiques.schema_export.export_all
::: boutiques.schema_export.VERSIONS

## Descriptor models

Pydantic models live under `boutiques.models.v05` and
`boutiques.models.v05_styx`. For day-to-day use, [`load`](#boutiques.loader.load)
returns the right one based on the descriptor's `schema-version`; the
models themselves are documented mostly via the
[specification](../spec/index.md). The JSON Schema artifacts under
`docs/schema/` are generated from these models.
