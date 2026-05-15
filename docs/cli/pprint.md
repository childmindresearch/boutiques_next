# `bosh pprint`

Render a descriptor as a structured tree view — easier to read than the
raw JSON, especially for descriptors with many inputs or nested
sub-commands.

```sh
bosh pprint <descriptor> [--no-color]
```

| Flag | Description |
| --- | --- |
| `--no-color` | Force ANSI colour off. Auto-detected when stdout is not a terminal. |

## Example output

```
$ bosh pprint fsl_bet.json
fsl_bet v1.0.0 (0.5)
Automated brain extraction tool for FSL
├── command-line: bet [INPUT_FILE] [MASK] [FRACTIONAL_INTENSITY] ...
├── container: docker index.docker.io/mcin/docker-fsl:latest
├── inputs (21)
│   ├── infile (File, required) [INPUT_FILE]
│   │   └── Input image (e.g. img.nii.gz)
│   ├── maskfile (String, required) [MASK]
│   │   └── Output brain mask
│   ├── fractional_intensity (Number, optional) -f [FRACTIONAL_INTENSITY]
│   │   ├── Fractional intensity threshold (0->1); default=0.5
│   │   └── range: [0.0, 1.0]
│   ├── center_of_gravity (Number, optional) -c [CENTER_OF_GRAVITY]
│   │   ├── ...
│   │   └── list: 3.0-3.0 entries, separator='space'
│   └── …
└── output-files (1)
    └── output_file (required)  [MASK]
```

## What it shows

For each input — type, optionality, command-line flag, value-key,
description, default value, numeric range (with `[` / `(` brackets for
inclusive / exclusive bounds), value choices, list bounds, and any
`requires-inputs` / `disables-inputs` declarations.

For sub-command unions, each candidate body is rendered as its own
sub-tree with its own command-line and inputs.

For outputs — id, required/optional, path-template (or "conditional"
marker), description, and any `path-template-stripped-extensions`.

Top-level extras when present: container image, groups, environment
variables, error codes, tests, stdout-output / stderr-output.

## Python equivalent

```python
from boutiques import load
from boutiques.prettyprint import pprint

pprint(load("fsl_bet.json"))           # to stdout
```

`build_tree(descriptor)` returns the `rich.tree.Tree` directly if you
want to embed it in a larger rendering.
