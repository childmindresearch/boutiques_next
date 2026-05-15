# `bosh test`

Run the test cases embedded in a descriptor's `tests` field.

```sh
bosh test <descriptor> [-r local|docker|singularity] [--cwd DIR]
```

For each test case, the runner:

1. Launches the tool with the test's `invocation` (using the selected
   runtime).
2. Compares the actual exit code against `assertions.exit-code` if set.
3. For each declared output in `assertions.output-files`:
   - verifies the resolved path exists,
   - if `md5-reference` is set, computes the file's MD5 and compares.

## Test case shape

Each entry in the descriptor's `tests` array looks like:

```json
{
  "name": "basic_run",
  "invocation": {
    "input_file": "tests/fixtures/in.nii",
    "output_prefix": "out"
  },
  "assertions": {
    "exit-code": 0,
    "output-files": [
      { "id": "result", "md5-reference": "c4ca4238a0b923820dcc509a6f75849b" }
    ]
  }
}
```

At least one of `exit-code` or `output-files` must be set; both can be
set in the same assertion.

## Output

```
$ bosh test descriptor.json
[PASS] basic_run (0.04s)
[FAIL] with_compression (0.05s)
        exit-code: expected 0, got 2
        output-files: 'compressed' expected at /work/out.gz but is missing

[bosh test] my_tool: 1 passed, 1 failed (of 2)
```

The CLI exits `0` if every test passes, `1` if any fails, `2` for
runtime errors (e.g. docker not installed).

## Python equivalent

```python
from boutiques import load
from boutiques.run_tests import run_tests

descriptor = load("descriptor.json")
results = run_tests(descriptor, runtime="docker")

if not results.passed:
    for case in results.cases:
        if not case.passed:
            print(case.name, case.failures)
```

`run_tests` returns a `TestRunResults` with `cases: list[TestCaseResult]`,
plus helpers `passed`, `num_passed`, `num_failed`.

## Limitations

- **Stdio outputs.** Assertions on `stdout-output` / `stderr-output`
  ids report unsupported — the v0.5 spec's `md5-reference` is
  defined for files. Use `exit-code` assertions and post-run
  inspection of `LaunchResult.stdout` for stdio checks.
- **Conditional path templates.** When an output uses
  `conditional-path-template` and none of the branches match, the
  resolved path is `None`; an existence assertion fails.
