# Roadmap

Scope tracker relative to the classic [`boutiques`](https://github.com/boutiques/boutiques)
Python package: what's shipped, what we've intentionally dropped, and
what's still open.

## Shipped

### Schema
- **Pydantic-first source of truth.** JSON Schema is generated from the
  models, not hand-written. Models live under `boutiques.models.v05` and
  `boutiques.models.v05_styx`.
- **v0.5 + v0.5+styx as a strict superset.** Every valid v0.5 descriptor
  loads as v0.5+styx; the styx variant additionally accepts SubCommand
  hierarchy, SubCommandUnion alternation, and Styx-spec FileInput
  attributes (`mutable`, `resolve-parent`).
- **Relaxed `tool-version` in v0.5+styx** for niwrap-style descriptors
  that carry version metadata in sidecar packaging. Surfaces as a lint
  warning instead of a hard error.
- **`stdout-output` / `stderr-output`** (v0.5+styx) — declare the
  tool's stdout/stderr as named outputs; captured content surfaces in
  `LaunchResult.outputs[*].content`.
- **JSON Schema export** for both versions via `boutiques.schema_export`.

### Validation (three tiers)
- **Structural** — Pydantic parsing; shape and types.
- **Semantic** (`boutiques.semantic`) — cross-field rules from the v0.5
  `dependencies` block plus descriptor-wide invariants:
  unique input IDs (per scope), unique value-keys (per scope), value-keys
  must appear in their command-line, unique output IDs, unique
  path-templates, orphan `[UPPER_CASE]` token detection, group members
  must reference real inputs, SubCommandUnion candidate IDs must be
  unique, min ≤ max, min-list ≤ max-list, and all the `requires`
  dependency rules.
- **Lint** (`boutiques.lint`) — soft advisories: recommend
  `tool-version` and `container-image`, value-key `[UPPER_CASE]`
  convention, Windows-unsafe path-template chars, repeated `[KEY]` in
  one command-line.

### CLI (`bosh`)
- `bosh validate <descriptor>` — three-tier output, exit 0/1.
- `bosh example <descriptor> [--complete]` — sample invocation JSON.
- `bosh exec simulate <desc> <invocation>` — resolved shell-safe
  command-line string.
- `bosh exec launch <desc> <invocation> [-r runtime] [--cwd dir]
  [--runtime-args "…"]` — actually runs it.
- `bosh schema-export [--output DIR] [--version V] [--stdout]` — emits
  the JSON Schema for one or both versions, ready for hosting.
- `bosh version`.
- All commands accept paths *or* http(s) URLs; GitHub blob URLs are
  auto-rewritten to raw.

### Execution
- **Dynamic invocation model** — per descriptor, build a Pydantic model
  via `create_model()` whose fields mirror the inputs (with `Literal`
  for choices, optional, list, recursive sub-commands as discriminated
  unions). Yields free type-checking with structured Pydantic errors.
- **shlex tokenization** — `resolve()` returns `list[str]` (argv);
  `simulate()` displays via `shlex.join()`. Values with spaces stay as
  one argv token; `--input=value` glues correctly; lists with custom
  separators glue, lists with the default space separator expand.
- **Local / Docker / Singularity (Apptainer) runtimes** — all live.
  Docker images launch under singularity via the `docker://` URI.
- **Live streaming** — Popen + two-thread drain; output streams to the
  terminal while still being captured into `LaunchResult.stdout/stderr`.
- **`--runtime-args` pass-through** for arbitrary container-runtime
  flags (e.g. `--gpus all`, `--network host`).
- **Auto-mounting** of file-input parent directories into the container
  (`-v` for docker, `--bind` for singularity), descendants deduped.
- **Output path resolution** — `path-template` substitution with
  `path-template-stripped-extensions`; `conditional-path-template` via a
  whitelisted AST evaluator (no `eval` on raw descriptor strings).
- **Environment variables** declared on the descriptor reach the
  subprocess and the container env.

### Quality
- ruff lint + format clean (strict-ish ruleset).
- mypy strict clean.
- 117 tests covering load, validate, lint, semantic checks, invocation
  model, resolution, sub-commands, mounts, outputs, stdio outputs, URL
  loading, shadow names, runtimes, and end-to-end launch.
- **CI workflow** (`.github/workflows/ci.yml`) runs ruff + mypy +
  pytest across Python 3.11 and 3.13 on push and PR.
- **Docs workflow** (`.github/workflows/docs.yml`) generates JSON
  Schema artifacts via `bosh schema-export`, builds the mkdocs site
  with `--strict`, and publishes to GitHub Pages on every push to
  `main`.

## Intentionally dropped

These features from classic boutiques are gone because the project
direction or upstream consensus moved elsewhere:

- **`bosh pull` / `bosh push`** — per team consensus on the upstream
  issue, replaced by github-indexed descriptor repositories. URL loading
  + raw GitHub fetch covers the pull case directly.
- **Zenodo publisher, Nexus helpers, `dataHandler`** — backend coupling
  that no longer matches the descriptor-registry model.
- **`searcher`** — same; descriptors are found by repo/URL now.
- **`importer`** (CWL / BIDS-app / Docker → Boutiques conversion) —
  out of scope for this rewrite. May return if a real need surfaces.
- **`exporter`** — same.
- **`creator`** — the interactive descriptor wizard. Out of scope.
- **`descriptor2func`** — superseded by the dynamic invocation model
  (which gives a typed Pydantic class per descriptor at runtime).
- **`boshParsers.py` argparse spaghetti** — replaced by Typer.
- **The 1605-line `localExec.py`** — replaced by `~400 LOC` across
  `execution/{launch,resolve,outputs,mounts,runtime/*}`.

## Open

### Near-term
- **Pre-commit hooks** mirroring the CI checks (ruff lint + format,
  mypy, pytest).

### Medium-term
- **Runtime invocation enforcement** for: `value-choices` range checks
  beyond structural Literal, `disables-inputs` / `requires-inputs`,
  `value-disables` / `value-enables`, group constraints
  (mutually-exclusive / one-is-required / all-or-none). Currently only
  enforced at semantic-validation time, not at invocation time.
- **`bosh test`** runner using the descriptor's `tests` field
  (invocations + assertions like `exit-code` and `output-files` MD5).
- **Better Pydantic error messages.** Pydantic's default dump is dense;
  pretty-print errors in the CLI (location → message lines, with `rich`
  coloring).
- **Container health check** (analogous to niwrap's `check_container`)
  — verify the image is pullable and the tool is on PATH inside it.

### Nice-to-have / longer-term
- **Smarter container mounts.** Currently mount each file-input's parent
  dir; classic boutiques is a bit cleverer about path rewriting. Revisit
  when a real descriptor breaks under current behavior.
- **`--no-stream` / `--no-capture` CLI flags.** Both already exist in
  the Python API; expose them on the CLI when someone asks.
- **HTTP fetch cache** for repeated URL loads (currently re-fetches
  every time).
- **`prettyprint`** equivalent for descriptors — table/tree view.
- **`deprecate`** equivalent — workflow for marking descriptors
  deprecated.
- **BIDS-app integration helper** (was `bids.py`) — only if needed.

## Non-goals

- **Compiling descriptors to language bindings.** That's Styx's job;
  this project consumes Styx-extended descriptors but does not generate
  Python/TS/R wrappers.
- **A descriptor authoring GUI.**
- **Hosting infrastructure for descriptor distribution.** Just consume
  github-indexed repos.
