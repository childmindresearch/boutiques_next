<p align="center">
  <img src="docs/logo.svg" alt="Boutiques" width="140">
</p>

# boutiques

> [!NOTE]
> **This is a proposed next-generation rewrite** of the
> [classic boutiques](https://github.com/boutiques/boutiques) toolkit,
> being incubated under `childmindresearch/boutiques_next` while
> upstream discussion plays out at
> [boutiques/boutiques#751](https://github.com/boutiques/boutiques/issues/751).
> It is **not** the canonical Boutiques implementation today — for that,
> install the upstream `boutiques` package from PyPI. If consensus
> lands, this repository will merge back into `boutiques/boutiques`.

A Python toolkit and CLI for the
[Boutiques](https://boutiques.github.io/) descriptor standard.
Validate descriptors, generate sample invocations, simulate or launch
tools locally / in Docker / in Singularity, run descriptor test cases,
pretty-print, and emit JSON Schema artifacts.

Supports two schema versions:

- **0.5** — the original Boutiques specification.
- **0.5+styx** — a strict superset adding sub-command hierarchy and
  alternation, the `mutable` / `resolve-parent` File-input attrs, and
  `stdout-output` / `stderr-output` capture.

Status: early development. The CLI shape and Pydantic model layout are
stable enough to build against; some details may still shift. See
[ROADMAP.md](ROADMAP.md) for what's shipped, what's intentionally
dropped vs. classic boutiques, and what's open.

## Quick taste

```sh
$ bosh validate fsl_bet.json
OK: fsl_bet v1.0.0 (0.5)

$ bosh example fsl_bet.json > invocation.json

$ bosh exec simulate fsl_bet.json invocation.json
bet /path/to/infile example_maskfile

$ bosh exec launch fsl_bet.json invocation.json -r docker
```

Paths and `http(s)://` URLs are accepted everywhere; GitHub blob URLs
auto-rewrite to raw, so you can run against descriptors hosted in any
repo:

```sh
bosh validate https://github.com/styx-api/niwrap/blob/main/src/niwrap/fsl/6.0.4/bet/boutiques.json
```

## CLI commands

| Command | Purpose |
| --- | --- |
| `bosh validate` | Three-tier validation: structural / semantic / lint |
| `bosh example` | Generate a sample invocation JSON |
| `bosh exec simulate` | Resolve invocation → shell-safe command-line string |
| `bosh exec launch` | Run the tool (local / docker / singularity) with live output |
| `bosh test` | Run the test cases declared in the descriptor's `tests` field |
| `bosh pprint` | Tree view of a descriptor (inputs, outputs, container, …) |
| `bosh invocation` | Validate an invocation, or embed its schema into the descriptor |
| `bosh invocation-schema` | Emit the invocation JSON Schema for a descriptor |
| `bosh schema-export` | Emit the descriptor-level JSON Schema |
| `bosh version` | Print the installed version |

Every subcommand delegates to a Python function under `boutiques.*`, so
the CLI is reproducible in a few lines of Python — see the
[API reference](https://childmindresearch.github.io/boutiques_next/api/).

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

## Docs

Hosted site (pre-merge):
<https://childmindresearch.github.io/boutiques_next/>.

Or serve locally:

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
