# Troubleshooting

Common authoring mistakes and how to spot them. The toolkit's three
validation tiers (`bosh validate`) catch most of these — see the
[`bosh validate` reference](../cli/validate.md) for what each tier
covers.

## Schema-level errors

### Missing required fields

```
inputs: Field required
```

Make sure every required top-level field is present (`name`,
`description`, `command-line`, `schema-version`, `inputs`, plus
`tool-version` for v0.5).

### Wrong value type

```
inputs.0.minimum: Input should be a valid number
```

Numeric fields take numbers, not numeric strings. `"0.5"` is a string.

### Invalid ID

```
inputs.0.id: String should match pattern '^[0-9_a-zA-Z]+$'
```

IDs must be alphanumeric + underscores. `input-file` is invalid; use
`input_file`.

## Command-line formation issues

### Value-key not substituted

If the resolved command-line contains the literal `[VALUE_KEY]` instead
of a value, the value-key string in the input doesn't match the
command-line template (often a typo or case mismatch). The
[`bosh validate`](../cli/validate.md) semantic pass flags this:

```
inputs[0].value-key: value-key '[Input_File]' does not appear in the command-line 'tool [INPUT_FILE]'.
```

### Orphan tokens in the command-line

If the command-line template has a `[TOKEN]` that no input declares as
its value-key, that token will appear literally in the executed
command. Semantic validation flags this too:

```
command-line: Command-line contains token [GHOST] with no matching input value-key.
```

### Flag missing from the resolved command

`command-line-flag` is the flag string itself (`-v`, `--threshold`).
`value-key` is the position in the template. Both are typically
needed:

```json
{
  "id": "verbose",
  "type": "Flag",
  "command-line-flag": "-v",
  "value-key": "[VERBOSE]"
}
```

A `Flag` input always needs `command-line-flag` (it has no value to
emit otherwise).

### List items joined wrong

By default lists become multiple argv tokens (joined with whitespace).
For a single token like `1.0,2.0,3.0`, set `list-separator`:

```json
{
  "id": "coords",
  "type": "Number",
  "list": true,
  "list-separator": ",",
  "value-key": "[COORDS]"
}
```

See [Advanced features](advanced_features.md#list-separator).

## Sub-command issues

### Invocation missing the `@type` discriminator

For a `SubCommandUnion` input, the invocation must include `@type` so
the loader can pick the right sub-command's schema:

```json
{ "op": { "@type": "blur", "sigma": 1.5 } }
```

Without `@type`, Pydantic reports the union-discrimination failure.
(The discriminator is named `@type` to match the Styx convention, so
invocations are portable between this toolkit and Styx-generated
language bindings.)

### Duplicate `id` across union candidates

Within a sub-command union, candidate `id`s become the `@type` values
in invocations. The loader rejects descriptors where two candidates
share an id with a `Sub-command union candidates must have unique
ids` error.

### Sub-command inputs leak the parent value-keys

A nested sub-command has its own scope for value-keys. The parent's
`[VALUE_KEY]` doesn't substitute inside the child's command-line. If
you need the same value at both levels, declare the input on the side
that owns the command-line.

## File handling issues

### Input file not found inside the container

`bosh exec launch -r docker|singularity` auto-mounts the parent
directory of every File-typed input value. If your file lives in a
location the container can't see otherwise (e.g. behind a symlink
chain), make sure the actual host path is the one in the invocation —
the toolkit calls `Path.resolve()` before mounting.

### Output file has a doubled extension

```
subject1.nii.gz_mask.nii.gz
```

Add `path-template-stripped-extensions` to remove the input's extension
before substitution:

```json
{
  "id": "output_mask",
  "path-template": "[INPUT]_mask.nii.gz",
  "path-template-stripped-extensions": [".nii.gz", ".nii"]
}
```

### Output reported as missing

The output's `path-template` is rendered relative to `--cwd` and
checked for existence after the run. If the tool actually wrote the
file elsewhere, the path-template doesn't match reality — adjust the
template (use the same value-keys the tool uses to construct the path).

## Container issues

### `docker runtime requires the descriptor to declare a container-image`

`-r docker` (or `singularity`) needs `container-image` in the
descriptor. Use `-r local` if you really do want to run on the host,
otherwise add a `container-image` block.

### Image not pullable

```
Error response from daemon: pull access denied for ...
```

Check the image name + tag, and whether you're authenticated against
the registry. Use `--runtime-args "--pull always"` (docker) to force a
fresh pull if you suspect a stale cache.

## Common pitfalls

### Confusing `value-key` and `command-line-flag`

- `value-key` — the placeholder in the command-line template.
- `command-line-flag` — the actual `-v` / `--option` string emitted
  before the value at substitution time.

Most inputs that aren't positional use both.

### Confusing input File vs. output paths

- Input files: `"type": "File"` inside `inputs`. The runtime treats
  them as paths to mount.
- Output paths used as arguments to the tool: `"type": "String"`
  inputs. The runtime treats them as opaque strings.
- Declared outputs: live in `output-files` with a `path-template`.
  They're specifications, not arguments.

### Inconsistent input naming

```
// Mix that's hard to read:
"id": "inputFile"
"id": "output-dir"
"id": "THRESHOLD"
```

Stick to a single style. Snake-case (`input_file`, `output_dir`) is
the most common.

## Debugging the resolved command

`bosh exec simulate <descriptor> <invocation>` prints the resolved
command-line without running it — the fastest way to see how an
invocation maps to argv:

```sh
$ bosh exec simulate descriptor.json invocation.json
bet /data/in.nii out.nii -f 0.5 -v
```

For the underlying argv list (instead of the joined string), use the
Python API:

```python
from boutiques import load
from boutiques.execution import resolve

print(resolve(load("descriptor.json"), invocation_dict))
# ['bet', '/data/in.nii', 'out.nii', '-f', '0.5', '-v']
```
