# `bosh validate`

Check a descriptor against the schema, semantic rules, and lint
advisories.

```sh
bosh validate <descriptor>
```

The `<descriptor>` argument is a local path or an `http(s)://` URL.

## What it checks

Three tiers run in order; the first tier that fails short-circuits.

1. **Structural** — Pydantic parsing. Required fields present, types
   correct, list bounds respected.
2. **Semantic** — cross-field rules. Examples: every input's
   `value-key` must appear in the command-line, output IDs must be
   unique within a scope, `exclusive-minimum` requires `minimum` to be
   set, group members must reference real input IDs.
3. **Lint** — soft advisories. The descriptor still validates, but a
   recommended field (e.g. `tool-version`, `container-image`) is
   missing, or a stylistic convention (e.g. `[UPPER_CASE]` value-keys)
   is violated.

## Output

On success:

```
$ bosh validate fsl_bet.json
OK: fsl_bet v1.0.0 (0.5)
```

On success with lint warnings:

```
$ bosh validate niwrap_tool.json
OK: @2dwarper v? (0.5+styx)
[warning] tool-version: Recommended: declare tool-version so the descriptor is self-contained...
[warning] container-image: Recommended: declare a container-image so the tool can be launched reproducibly...
```

On failure, each error is reported with a JSON-pointer-style location:

```
$ bosh validate broken.json
inputs[0].value-key: value-key '[X]' does not appear in the command-line 'tool '.
```

Exit code is `0` on OK (even with warnings) and `1` on errors.

## Python equivalent

```python
from boutiques import validate

result = validate("fsl_bet.json")
print(result.ok)        # True
print(result.warnings)  # [LintIssue, ...]
print(result.errors)    # []
```
