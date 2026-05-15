# `bosh schema-export`

Generate the JSON Schema for one or both supported schema versions.

```sh
bosh schema-export [--output DIR] [--version VERSION]
```

| Flag | Default | Description |
| --- | --- | --- |
| `-o`, `--output` | — *(prints to stdout)* | Directory to write `descriptor.schema.json` files into. |
| `--version` | `0.5+styx` *(stdout mode)* / *(both)* *(disk mode)* | Limit output to a single version (`0.5` or `0.5+styx`). |

Without `-o`, the schema is printed to stdout (one version per
invocation; defaults to `0.5+styx`). With `-o`, the file is written to
disk; if `--version` is omitted, every known version is written.

## Examples

```sh
# Print the v0.5+styx schema (default) to stdout
bosh schema-export

# Pipe to jq
bosh schema-export --version 0.5 | jq .properties

# Write both versions to docs/schema/0.5/ and docs/schema/0.5+styx/
bosh schema-export -o docs/schema

# Just one version to disk
bosh schema-export --version 0.5 -o build/schemas
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
