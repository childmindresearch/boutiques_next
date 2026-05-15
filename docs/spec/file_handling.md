# File handling

How input file paths are passed to a tool, and how output file paths
are declared and resolved.

## Input files

Use `type: "File"` for inputs that take a file path:

```json
{
  "id": "image",
  "name": "Input image",
  "type": "File",
  "value-key": "[INPUT]",
  "optional": false
}
```

### Container mounting

When `bosh exec launch` runs a descriptor under a container runtime
(`docker` or `singularity`), every File-typed input's parent directory
is automatically bind-mounted into the container at the same path.
Descendant paths are deduped, so a list of files all under the same
parent yields a single mount. The working directory is always mounted
as well.

This means the descriptor doesn't need to know anything about the
host/container path mapping — input paths inside the container match
their host paths verbatim.

### File-only attributes

| Field | Available in | Description |
| --- | --- | --- |
| `uses-absolute-path` | 0.5 + 0.5+styx | The file path must be absolute. |
| `mutable` | 0.5+styx | The tool may modify the input file in place. |
| `resolve-parent` | 0.5+styx | The parent directory of the file must be visible to the tool, not just the file itself. |

`list: true` works on File inputs to take multiple paths:

```json
{
  "id": "volumes",
  "name": "Input volumes",
  "type": "File",
  "value-key": "[VOLUMES]",
  "list": true,
  "min-list-entries": 1
}
```

## Output files

Outputs are declared in the `output-files` array. They are not passed
to the command-line — they describe what the tool *will produce* so
downstream tooling can locate and validate the results.

```json
"output-files": [
  {
    "id": "brain_mask",
    "name": "Brain mask",
    "path-template": "[OUTPUT].mask.nii.gz",
    "optional": false
  }
]
```

### Path templates

`path-template` is a string with value-key placeholders from the inputs:

```json
"inputs": [
  { "id": "output_dir", "type": "String", "value-key": "[OUTDIR]" },
  { "id": "subject_id", "type": "String", "value-key": "[SUBJECT]" }
],
"output-files": [
  {
    "id": "processed_image",
    "name": "Processed image",
    "path-template": "[OUTDIR]/sub-[SUBJECT]/anat/image.nii.gz"
  }
]
```

Templates are resolved at launch time by substituting each value-key
with its invocation value. The resolved path is then anchored at the
launch's working directory (`--cwd`).

### Extension stripping

A common pattern is to produce an output named after an input but with
a different extension. `path-template-stripped-extensions` strips the
listed extensions from input values *before* they are substituted into
the template:

```json
"inputs": [
  { "id": "input_image", "type": "File", "value-key": "[INPUT]" }
],
"output-files": [
  {
    "id": "output_mask",
    "name": "Output mask",
    "path-template": "[INPUT]_mask.nii.gz",
    "path-template-stripped-extensions": [".nii.gz", ".nii", ".img", ".hdr"]
  }
]
```

If the input is `subject1.nii.gz`, the output resolves to
`subject1_mask.nii.gz` — not `subject1.nii.gz_mask.nii.gz`.

### Conditional path templates

`conditional-path-template` picks a path based on the invocation values
via a limited boolean expression dialect:

```json
{
  "id": "report",
  "name": "Report",
  "conditional-path-template": [
    { "[SIZE] > 1000": "large_report.html" },
    { "[SIZE] > 100":  "medium_report.html" },
    { "default":       "small_report.html" }
  ]
}
```

Entries are evaluated in order; the first matching expression wins.
`"default"` is the fallback. If no entry matches and there is no
default, the output's resolved path is reported as `None`.

The expression dialect is a strict subset of Python: comparisons
(`==`, `!=`, `<`, `>`, `<=`, `>=`), logical operators (`and`, `or`,
`not`), unary `+`/`-`, and constants. Function calls, attribute access,
and names are rejected by an AST allowlist before evaluation. Strings
are interpolated as Python literals, so `[MODE] == 'fast'` works.

### Common output fields

| Field | Description | Required | Example |
| --- | --- | --- | --- |
| `id` | Unique identifier. | Yes | `"brain_mask"` |
| `name` | Human-readable name. | Yes | `"Brain mask"` |
| `description` | Free-form description. | No | `"Binary mask of the brain."` |
| `path-template` | Template for the output path. Mutually exclusive with `conditional-path-template`. | Yes (one of) | `"[PREFIX]_mask.nii.gz"` |
| `conditional-path-template` | Expression-driven path selection. | Yes (one of) | See above |
| `path-template-stripped-extensions` | Extensions stripped from input values before substitution. | No | `[".nii.gz", ".nii"]` |
| `optional` | Whether the file may not be produced. | No | `true` |
| `list` | True if the output is a list of files. | No | `true` |

## Sub-command output files

Each sub-command body declares its own `output-files`; outputs are
scoped to the sub-command the invocation selects. See
[Subcommands](subcommands.md) for the full picture.

## Capturing stdout and stderr (v0.5+styx)

Some tools emit their primary output to stdout (or report structured
warnings on stderr) rather than writing a file. Two top-level
descriptor fields declare these streams as named outputs:

```json
{
  "stdout-output": {
    "id": "coordinates",
    "name": "Extracted coordinates",
    "description": "Tab-separated coordinate values."
  },
  "stderr-output": {
    "id": "warnings",
    "name": "Warning log"
  }
}
```

Each declaration has the same shape: a required `id`, optional `name`,
and optional `description`. They are not nested inside `output-files`
because they don't have a path — the captured text *is* the output.

After `bosh exec launch` runs, the captured content surfaces in
`LaunchResult.outputs` as `ResolvedOutput` entries whose `path` is
`None` and whose `content` field carries the text. The raw streams are
still available via `LaunchResult.stdout` / `LaunchResult.stderr` for
callers that don't care about the named declaration.

## Best practices

- Use `File` for input file paths, `String` for output path *arguments*
  that get passed on the command-line. Declared outputs use
  `path-template`, not a `File` input.
- Keep output paths flexible by referencing input value-keys.
- Use `path-template-stripped-extensions` whenever the output extension
  differs from the input's.
- Mark outputs `optional: true` if the tool may not produce them in all
  modes.
