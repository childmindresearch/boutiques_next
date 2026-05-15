# Basic structure

A Boutiques descriptor is a JSON file with a fixed top-level shape and
a list of inputs. This page covers the required fields, the four input
types, how command-lines are formed, and how output files are declared.

## Top-level fields

### Required

| Field | Description | Example |
| --- | --- | --- |
| `name` | Short name of the tool. | `"bet"` |
| `description` | What the tool does. | `"Brain extraction tool for FSL"` |
| `schema-version` | Descriptor format version. | `"0.5+styx"` |
| `command-line` | Template with `[VALUE_KEY]` placeholders. | `"bet [INFILE] [MASKFILE] [OPTIONS]"` |
| `inputs` | Array of input parameters (at least one). | `[{ "id": "infile", ... }]` |
| `tool-version` | Version of the tool being wrapped. *Optional under v0.5+styx* — descriptor-registry workflows often carry the version in sidecar packaging. | `"6.0.5"` |

### Common optional

| Field | Description | Example |
| --- | --- | --- |
| `author` | Author of the tool. | `"FMRIB Analysis Group, University of Oxford"` |
| `url` | Documentation URL. | `"https://fsl.fmrib.ox.ac.uk/fsl/fslwiki"` |
| `descriptor-url` | URL where the descriptor itself lives. | `"https://github.com/.../bet.json"` |
| `output-files` | Declared output files. | `[{ "id": "outfile", ... }]` |
| `stdout-output` | *(v0.5+styx)* Declare the tool's stdout as a named output. See [File handling](file_handling.md#capturing-stdout-and-stderr-v05styx). | `{ "id": "results" }` |
| `stderr-output` | *(v0.5+styx)* Declare the tool's stderr as a named output. | `{ "id": "log" }` |
| `container-image` | Container image declaration. See [Advanced features](advanced_features.md#container-images). | `{ "type": "docker", "image": "fsl/bet" }` |
| `environment-variables` | Variables to set in the execution environment. | `[{ "name": "FSLOUTPUTTYPE", "value": "NIFTI_GZ" }]` |
| `groups` | Mutual-exclusion / one-required constraints across inputs. See [Advanced features](advanced_features.md#groups). | `[{ "id": "mode", ... }]` |
| `suggested-resources` | CPU / RAM / walltime hints. | `{ "cpu-cores": 4, "ram": 8 }` |
| `error-codes` | Documented exit codes. | `[{ "code": 2, "description": "I/O error" }]` |
| `tests` | Sample invocations with assertions. | `[{ "name": "basic", ... }]` |
| `tags` | Free-form key/value tags. | `{ "domain": "neuroimaging" }` |
| `custom` | Tool-specific extension fields outside the spec. | `{ ... }` |

## Input parameters

Inputs live in the top-level `inputs` array. Each input shares a set of
common fields and then adds type-specific ones.

### Common input fields

| Field | Description | Required | Example |
| --- | --- | --- | --- |
| `id` | Unique identifier; alphanumeric + underscores. | Yes | `"input_file"` |
| `name` | Human-readable name. | Yes | `"Input file"` |
| `type` | One of `String`, `File`, `Number`, `Flag` (plus the styx sub-command shapes; see [Subcommands](subcommands.md)). | Yes | `"File"` |
| `value-key` | Token in the command-line template this input substitutes for. By convention `[UPPER_CASE]`. | Yes (for substitutable inputs) | `"[INPUT_FILE]"` |
| `description` | Free-form description. | No | `"The input image in NIfTI format."` |
| `optional` | Whether the input may be omitted. | No (default `false`) | `true` |
| `command-line-flag` | Flag emitted before the value. | No | `"-i"` |
| `command-line-flag-separator` | Character between flag and value. Default is a single space. Set to `"="` for `--input=value` form. | No | `"="` |
| `default-value` | Default if not specified. Use sparingly: this *overrides* the tool's own default in downstream wrappers; only set it when you genuinely want to change the tool's default behaviour. | No | `0.5` |
| `value-choices` | Closed set of permitted values (`String` or `Number` only). | No | `["small", "medium", "large"]` |

### Input types

| Type | Description | Type-specific attributes |
| --- | --- | --- |
| `File` | A file path. | `uses-absolute-path` (bool); in v0.5+styx, `mutable` (bool) and `resolve-parent` (bool). |
| `String` | A text value. | `value-choices`. |
| `Number` | A numeric value. | `integer` (bool — default float), `minimum`, `maximum`, `exclusive-minimum`, `exclusive-maximum`, `value-choices`. |
| `Flag` | A boolean toggle. Always carries a `command-line-flag`; emits the flag if true. | — |

### List variants

Any input can be made a list by adding `"list": true`:

```json
{
  "id": "coordinates",
  "type": "Number",
  "list": true,
  "min-list-entries": 3,
  "max-list-entries": 3,
  "value-key": "[COORDS]"
}
```

Optional list-related fields:

- `min-list-entries` / `max-list-entries` — bounds on the list length.
- `list-separator` — character(s) used to join the items in the
  rendered command-line. Defaults to a single space.

`Flag` inputs cannot be lists.

## Command-line formation

The runtime takes the descriptor's `command-line` template, substitutes
each input's `value-key` with its rendered form, and produces an argv
list (see the [CLI exec docs](../cli/exec.md) for the tokenisation
algorithm).

### Value keys

By convention value-keys are enclosed in square brackets and use only
uppercase letters, numbers, and underscores: `[INFILE]`,
`[OUTPUT_DIR]`. They must match exactly between the input's
`value-key` and the `command-line` template.

```json
"command-line": "bet [INFILE] [OUTFILE]",
"inputs": [
  { "id": "infile", "value-key": "[INFILE]", "type": "File" },
  { "id": "outfile", "value-key": "[OUTFILE]", "type": "String" }
]
```

### Flags

For inputs that prefix their value with an option flag, set
`command-line-flag`:

```json
{
  "id": "verbose",
  "type": "Flag",
  "command-line-flag": "-v",
  "value-key": "[VERBOSE]"
}
```

For non-flag inputs, the separator between flag and value defaults to a
single space (so the flag and value become two argv tokens). Set
`command-line-flag-separator` to `"="` to glue them into one token:

```json
{
  "id": "threshold",
  "type": "Number",
  "command-line-flag": "--threshold",
  "command-line-flag-separator": "=",
  "value-key": "[THRESHOLD]"
}
```

Resolved: `--threshold=0.5` (one argv token) instead of `--threshold 0.5`.

## Output files

The `output-files` array declares what the tool produces. These are
*specifications* (used to resolve paths and check existence) — they are
not command-line arguments.

```json
"output-files": [
  {
    "id": "brain_mask",
    "name": "Brain mask",
    "description": "Binary mask of the brain.",
    "path-template": "[OUTDIR]/[PREFIX]_mask.nii.gz",
    "optional": false
  }
]
```

The `path-template` uses input value-keys to construct the output path
at runtime. See [File handling](file_handling.md) for path-template
substitution rules, extension stripping, and conditional templates.

### Common output fields

| Field | Description | Required | Example |
| --- | --- | --- | --- |
| `id` | Unique identifier. | Yes | `"brain_mask"` |
| `name` | Human-readable name. | Yes | `"Brain mask"` |
| `description` | Free-form description. | No | `"Binary mask of the brain."` |
| `path-template` | Template for the output path; mutually exclusive with `conditional-path-template`. | Yes (one of) | `"[PREFIX]_mask.nii.gz"` |
| `conditional-path-template` | Path chosen based on input values via a limited boolean DSL. See [File handling](file_handling.md#conditional-path-templates). | Yes (one of) | `[{ "[N] > 8": "big.txt" }, { "default": "small.txt" }]` |
| `optional` | Whether the file may not be produced. | No | `true` |
| `path-template-stripped-extensions` | Extensions to strip from input values before substituting them into the template. | No | `[".nii.gz", ".nii"]` |

## Where to go next

- [Subcommands](subcommands.md) for tools with complex sub-command
  structure (e.g. `mri_tool blur ...` vs `mri_tool sharpen ...`).
- [File handling](file_handling.md) for input/output file mechanics.
- [Advanced features](advanced_features.md) for groups, containers, and
  constraints.
- [Examples](examples.md) for complete worked descriptors.
- [Troubleshooting](troubleshooting.md) for common gotchas.
