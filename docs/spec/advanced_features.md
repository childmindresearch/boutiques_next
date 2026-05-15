# Advanced features

Fields and patterns beyond the basics — container declarations, groups,
constraints, and the various separator knobs.

## Container images

`container-image` declares how the tool should be executed under a
container runtime:

```json
"container-image": {
  "type": "docker",
  "image": "brainlife/fsl:6.0.4-patched2",
  "index": "docker.io"
}
```

| Field | Description |
| --- | --- |
| `type` | `"docker"`, `"singularity"`, or `"rootfs"`. |
| `image` | Image name (for `docker` / `singularity` types). |
| `url` | URL of the rootfs image (`rootfs` type). |
| `index` | Optional registry override. Example: `"docker.io"`. |
| `entrypoint` | True if the container defines an entrypoint. |
| `working-directory` | Location from which the task must be launched inside the container. |
| `container-hash` | Hash of the image for reproducibility. |
| `container-opts` | Extra container-level arguments. Example: `["--privileged"]`. |

When `bosh exec launch` runs with `-r docker` it uses these fields to
construct the `docker run` invocation. With `-r singularity` it
constructs a `singularity exec docker://<image>` (or, for `rootfs`
type, points directly at the rootfs URL).

### Why declare a container?

The toolkit also lints descriptors without a `container-image`. It's
not required by the v0.5 spec, but a descriptor without one cannot be
reproducibly launched in a container runtime — the consumer has to
supply the image themselves.

## Groups

Groups define cross-input constraints on the *top-level* inputs array:

```json
"groups": [
  {
    "id": "exclusive_options",
    "name": "Processing options",
    "description": "Choose only one processing option.",
    "members": ["fast_mode", "accurate_mode", "balanced_mode"],
    "mutually-exclusive": true
  },
  {
    "id": "logging",
    "name": "Logging flags",
    "members": ["verbose", "debug", "trace"],
    "one-is-required": false
  }
]
```

| Field | Description |
| --- | --- |
| `id` | Unique identifier. |
| `name` | Human-readable name. |
| `description` | Free-form description. |
| `members` | IDs of inputs belonging to the group. |
| `mutually-exclusive` | At most one member may be active. |
| `one-is-required` | At least one member must be active. |
| `all-or-none` | Either all members are active or none. |

Group members must reference real input IDs; the toolkit's semantic
validation rejects descriptors where they don't.

!!! info "When to use groups vs. sub-commands"
    Use groups for simple toggle-style constraints across inputs of the
    same shape. Reach for [sub-commands](subcommands.md) when each
    option carries its own parameter set.

## Command-line flag separator

By default a flag and its value become two argv tokens. Set
`command-line-flag-separator` to `"="` (or any non-whitespace string)
to glue them into one:

```json
{
  "id": "threshold",
  "type": "Number",
  "command-line-flag": "--threshold",
  "command-line-flag-separator": "=",
  "value-key": "[THRESHOLD]"
}
```

Resolved: `--threshold=0.5` (one token) instead of `--threshold 0.5`
(two).

## List separator

For list inputs, items are joined with a single space by default. Use
`list-separator` to glue them into one token:

```json
{
  "id": "coordinates",
  "type": "Number",
  "list": true,
  "list-separator": ",",
  "value-key": "[COORDS]"
}
```

Resolved with `[1, 2, 3]`: `1,2,3` (one argv token) instead of `1 2 3`
(three argv tokens).

## Value constraints

### Numeric

```json
{
  "id": "threshold",
  "type": "Number",
  "integer": false,
  "minimum": 0,
  "maximum": 1,
  "exclusive-minimum": false,
  "exclusive-maximum": false
}
```

- `integer` — restrict to integer values (defaults to false: floats).
- `minimum` / `maximum` — bounds (inclusive by default).
- `exclusive-minimum` / `exclusive-maximum` — make the bound strict.
  Each requires the corresponding non-exclusive bound to be set.

### String

```json
{
  "id": "mode",
  "type": "String",
  "value-choices": ["fast", "balanced", "accurate"]
}
```

`value-choices` defines a closed set of permitted values. Available on
`String` and `Number` inputs.

### Dependencies between inputs

| Field | Effect |
| --- | --- |
| `requires-inputs` | IDs of inputs (or groups) that must be active for this input to be available. |
| `disables-inputs` | IDs of inputs that are disabled when this input is active. |
| `value-requires` | Per-value-choice IDs of inputs that must be active when that choice is selected. |
| `value-disables` | Per-value-choice IDs of inputs that are disabled when that choice is selected. |

`value-requires` / `value-disables` are only meaningful when
`value-choices` is set; the toolkit's semantic validation enforces
that.

## Environment variables

Variables to set in the execution environment:

```json
"environment-variables": [
  { "name": "FSLOUTPUTTYPE", "value": "NIFTI_GZ" },
  { "name": "OMP_NUM_THREADS", "value": "4" }
]
```

`bosh exec launch` passes these to the subprocess (local runtime) or as
`-e NAME=VALUE` / `--env NAME=VALUE` flags (docker / singularity).

## Suggested resources

Soft hints for downstream schedulers:

```json
"suggested-resources": {
  "cpu-cores": 4,
  "ram": 8,
  "disk-space": 20,
  "walltime-estimate": 1800
}
```

The toolkit reads these but does not enforce them.

## Error codes

Document the tool's exit-code semantics:

```json
"error-codes": [
  { "code": 1, "description": "I/O error." },
  { "code": 2, "description": "Invalid input." }
]
```

## Tests

Embedded test cases with assertions:

```json
"tests": [
  {
    "name": "basic",
    "invocation": { "input": "tests/in.nii", "output": "out.nii" },
    "assertions": {
      "exit-code": 0,
      "output-files": [{ "id": "output", "md5-reference": "abc123…" }]
    }
  }
]
```

A `bosh test` runner is on the roadmap.

## Tags and custom fields

- `tags` — open key/value pairs for categorisation.
  Example: `{ "domain": "neuroimaging", "modality": "MRI" }`.
- `custom` — escape hatch for tool-specific metadata that doesn't fit
  the spec.

Neither field has spec-defined semantics; both are passed through
verbatim.
