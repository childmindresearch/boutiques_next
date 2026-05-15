# Boutiques

A Python toolkit for the **Boutiques** descriptor standard — a JSON
format for describing command-line tools (inputs, outputs, container
images, etc.) in a structured, language-agnostic way.

This repository hosts both:

- **The specification** — described in
  [the Specification section](spec/index.md), with machine-readable JSON
  Schema artifacts under [Schema JSON](#).
- **The `bosh` CLI** — see the [CLI reference](cli/index.md).

Two schema versions are supported:

- **0.5** — the original Boutiques specification.
- **0.5+styx** — a strict superset of 0.5 adding sub-command hierarchy,
  sub-command alternation, and a couple of file-input attributes used by
  the [Styx](https://github.com/styx-api) ecosystem. Every valid 0.5
  descriptor is also a valid 0.5+styx descriptor (only the
  ``schema-version`` field changes).

## Install

```sh
uv add boutiques            # or: pip install boutiques
```

For development:

```sh
git clone https://github.com/childmindresearch/boutiques_next
cd boutiques_next
uv sync
uv run bosh --help
```

## Quickstart

Validate a descriptor:

```sh
bosh validate fsl_bet.json
```

Generate a sample invocation:

```sh
bosh example fsl_bet.json > invocation.json
```

See the command-line that would run, without running it:

```sh
bosh exec simulate fsl_bet.json invocation.json
```

Actually launch the tool (locally, in docker, or in singularity):

```sh
bosh exec launch fsl_bet.json invocation.json -r docker
```

URLs work everywhere paths do — including GitHub blob links, which get
auto-rewritten to raw:

```sh
bosh validate https://github.com/boutiques/boutiques/blob/main/example.json
```

## Status

Early development. The public Python API is not yet stable; the
descriptor spec is. See [the roadmap](https://github.com/childmindresearch/boutiques_next/blob/main/ROADMAP.md)
for what's shipped, what's intentionally dropped vs. classic boutiques,
and what's open.
