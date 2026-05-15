# `bosh invocation-schema`

Emit the JSON Schema describing valid **invocations** for a specific
descriptor. (For validating an invocation against that schema, see
[`bosh invocation`](invocation.md); for the *descriptor* schema, see
[`bosh schema-export`](schema-export.md).)

```sh
bosh invocation-schema <descriptor> [-o FILE]
```

| Flag | Description |
| --- | --- |
| `-o`, `--output` | File to write the schema into. Without `-o`, prints to stdout. |

## What's in the schema

The schema is derived from the descriptor's inputs and reflects
everything `bosh exec simulate` / `launch` enforces structurally:

- Required vs. optional inputs.
- Per-input types (`string`, `number`, `boolean`, list-of-X).
- `value-choices` as `enum`.
- Numeric ranges (`minimum` / `maximum` / `exclusive*`).
- List bounds (`minItems` / `maxItems`).
- Sub-command unions as discriminated `oneOf` branches keyed by `@type`
  (matches Styx's tagged-union convention).

Cross-input constraints (`requires-inputs`, group rules, `value-requires`,
…) are enforced at runtime but don't lower to JSON Schema; they belong
to `bosh exec` and `bosh invocation -i` only.

## Examples

```sh
# Pipe through jq
$ bosh invocation-schema fsl_bet.json | jq '.properties.infile'
{
  "title": "Infile",
  "type": "string"
}

# Save for distribution alongside the descriptor
$ bosh invocation-schema https://.../bet/boutiques.json -o bet.invocation.schema.json
Wrote bet.invocation.schema.json
```

## Python equivalent

```python
from boutiques import load
from boutiques.invocation import invocation_schema

schema = invocation_schema(load("descriptor.json"))
```

`invocation_schema(descriptor)` returns the JSON Schema dict directly;
`invocation_model_for(descriptor)` returns the underlying Pydantic
model class if you want to validate dicts programmatically without
materialising the schema.
