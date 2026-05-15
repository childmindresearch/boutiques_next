# `bosh invocation`

Validate an invocation against a descriptor, or embed the invocation
schema back into the descriptor file. Drop-in replacement for classic
boutiques' `bosh invocation`.

For dumping the invocation schema to stdout / a file, see
[`bosh invocation-schema`](invocation-schema.md).

```sh
bosh invocation <descriptor> [-i INVOCATION] [-w]
```

| Flag | Description |
| --- | --- |
| `-i`, `--invocation` | Validate this invocation file against the descriptor's schema. |
| `-w`, `--write-schema` | Embed the generated invocation schema into the descriptor file (under `invocation-schema`). Requires the descriptor to be a local path. |

## Behaviour

- **Plain mode** (no flags): confirms the descriptor's input shape is
  internally consistent — i.e. an invocation schema can be built. Prints
  `OK` on success, exits 1 otherwise.
- **`-i invocation.json`**: validates the given invocation against the
  schema using the same three layers `bosh exec simulate` runs
  (structural / cross-input / groups). Prints `OK` or the failing
  locations; exits 0/1.
- **`-w`**: computes the invocation schema and writes it back into the
  descriptor file as the `invocation-schema` field. The descriptor is
  re-serialized with two-space indentation. Useful when shipping
  descriptors with cached schemas; the toolkit itself generates the
  schema on the fly so caching is optional.

## Examples

```sh
# Sanity-check a descriptor
$ bosh invocation fsl_bet.json
OK

# Validate a specific invocation
$ bosh invocation fsl_bet.json -i invocation.json
fractional_intensity: Input should be less than or equal to 1

# Embed the schema for distribution
$ bosh invocation fsl_bet.json -w
Wrote invocation-schema into fsl_bet.json
```

## Python equivalent

```python
from boutiques import load
from boutiques.invocation_check import validate_invocation

descriptor = load("fsl_bet.json")
errors = validate_invocation(descriptor, {"infile": "/in.nii", "maskfile": "out.nii"})
if errors:
    for e in errors:
        print(e)
```

For the schema itself:
```python
from boutiques.invocation import invocation_schema
schema = invocation_schema(descriptor)
```
