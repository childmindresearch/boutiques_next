# CLI reference

The `bosh` command-line tool exposes five subcommands. All of them
accept either a local path or an `http(s)://` URL for the descriptor
argument; GitHub blob URLs are auto-rewritten to their raw form.

| Command | Purpose |
| --- | --- |
| [`bosh validate`](validate.md) | Check a descriptor against the schema, semantic rules, and lint advisories. |
| [`bosh example`](example.md) | Generate a sample invocation for a descriptor. |
| [`bosh exec simulate`](exec.md#simulate) | Resolve a descriptor + invocation into the command-line that would run, without running it. |
| [`bosh exec launch`](exec.md#launch) | Resolve and actually run the tool under a local, docker, or singularity runtime. |
| [`bosh test`](test.md) | Run the test cases embedded in the descriptor's `tests` field. |
| [`bosh pprint`](pprint.md) | Render a descriptor as a structured tree view. |
| [`bosh schema-export`](schema-export.md) | Emit the JSON Schema for one or both schema versions. |
| [`bosh invocation`](invocation.md) | Emit the invocation JSON Schema for a specific descriptor. |
| [`bosh version`](version.md) | Print the installed version. |

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Success (the underlying command's exit code, for `exec launch`). |
| `1` | Validation or descriptor load error. |
| `2` | Runtime error (e.g. docker not installed, image not pullable). |
| *n* | For `exec launch`, the exit code of the tool itself. |

## Python API

Every CLI command delegates to a Python function under the `boutiques.*`
namespace — see the [API reference](../api/index.md) (once published).
The CLI is deliberately thin: anything you can do at the command line
you can do in three lines of Python.

```python
from boutiques import validate, load
from boutiques.execution import launch

result = validate("descriptor.json")
if not result.ok:
    raise SystemExit(result.format())

descriptor = load("descriptor.json")
outcome = launch(descriptor, {"input_file": "/data/in.nii"}, runtime="docker")
```
