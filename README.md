<p align="center">
  <img src="docs/logo.svg" alt="Boutiques" width="140">
</p>

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
uv run pre-commit install   # one-time: register the git hook
```

Once `pre-commit install` is run, `ruff` (lint + format) and `mypy`
will run automatically on every `git commit` against the staged files,
plus a small set of hygiene hooks (trailing whitespace, end-of-file
fixer, YAML/TOML syntax, merge-conflict markers, large-file guard).
To run all hooks manually against the whole tree:

```sh
uv run pre-commit run --all-files
```

`pytest` is **not** in pre-commit (too slow for an every-commit gate);
CI runs it on push and PR.

## Docs site (local)

```sh
uv sync --group docs
uv run bosh schema-export -o docs/schema   # generate JSON Schema artifacts
uv run mkdocs serve                        # http://127.0.0.1:8000
```

## CI

GitHub Actions runs on every push and PR — see
[`.github/workflows/`](.github/workflows). The `ci` workflow runs
`ruff check`, `ruff format --check`, `mypy`, and `pytest` across
Python 3.11 and 3.13. The `docs` workflow exports the JSON Schemas,
builds the mkdocs site with `--strict`, and publishes to GitHub Pages
on push to `main`. Both use `uv` with the lockfile-pinned dependencies.

For Pages publishing to work, the repository must have GitHub Pages
configured to deploy from Actions (Settings → Pages → "Source: GitHub
Actions").
