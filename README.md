# boutiques

A Python toolkit for the [Boutiques](https://boutiques.github.io/) descriptor
standard: validate descriptors, generate sample invocations, simulate
command-lines, and launch tools under local, Docker, or Singularity runtimes.

This repository hosts both the **specification** (Pydantic models that produce
the canonical JSON Schema) and the **`bosh` CLI** that operates on it. Two
schema versions are supported:

- **0.5** — the original Boutiques specification.
- **0.5+styx** — a strict superset of 0.5 adding sub-commands (hierarchy),
  sub-command unions (alternation), and explicit list inputs (repetition).

Status: early development. The public API is not yet stable.

## Install (development)

```sh
uv sync
uv run bosh --help
uv run pytest
```

## Docs site (local)

```sh
uv sync --group docs
uv run bosh schema-export -o docs/schema   # generate JSON Schema artifacts
uv run mkdocs serve                        # http://127.0.0.1:8000
```
