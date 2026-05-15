# `bosh schema-export`

Generate the JSON Schema for one or both supported schema versions.

```sh
bosh schema-export [--output DIR] [--version VERSION] [--stdout]
```

| Flag | Default | Description |
| --- | --- | --- |
| `-o`, `--output` | `docs/schema` | Directory to write `descriptor.schema.json` files into. |
| `--version` | *(both)* | Limit output to a single version (`0.5` or `0.5+styx`). |
| `--stdout` | `false` | Print the schema to stdout instead of writing to disk. Requires `--version`. |

## Examples

```sh
# Write both versions to docs/schema/0.5/ and docs/schema/0.5+styx/
bosh schema-export

# Custom output directory
bosh schema-export -o build/schemas

# Just one version
bosh schema-export --version 0.5 -o build/schemas

# Pipe one schema to another tool
bosh schema-export --stdout --version 0.5+styx | jq .properties
```

## CI usage

This is the command CI runs before publishing the docs site, so the
generated JSON Schema artifacts land alongside the rest of the docs and
serve from stable URLs. While this lives under
`childmindresearch/boutiques_next`:

- `https://childmindresearch.github.io/boutiques_next/schema/0.5/descriptor.schema.json`
- `https://childmindresearch.github.io/boutiques_next/schema/0.5+styx/descriptor.schema.json`

Once merged upstream, these will flip to
`https://boutiques.github.io/boutiques/schema/…`.

## Python equivalent

```python
from pathlib import Path
from boutiques.schema_export import export_all, schema_for

# Programmatic schema dict
schema = schema_for("0.5+styx")

# Write both versions to disk
paths = export_all(Path("docs/schema"))
```
