# Subcommands

Sub-commands describe tools whose interface branches: different
sub-commands accept different parameter sets, and an invocation
selects one of them. They're a v0.5+styx extension.

Two shapes exist:

- **A single sub-command** — `type` is an object. Used for grouping
  related parameters that are always used together.
- **A sub-command union** — `type` is an array of objects. Used for
  mutually exclusive modes; the invocation picks exactly one.

Each sub-command body declares its own `command-line`, its own
`inputs`, and (optionally) its own `output-files`. Sub-commands can be
nested arbitrarily and made repeatable with `list: true`.

## Sub-command vs. groups

The v0.5 `groups` field with `mutually-exclusive: true` can express
"pick one of these inputs." Sub-commands generalise that:

- Each option gets its own parameter set, not just an "active or not"
  toggle.
- Each option can declare its own outputs.
- The invocation structure mirrors the descriptor structure, so
  validation is structural rather than constraint-driven.

Groups remain part of the spec for other patterns (`one-is-required`,
`all-or-none`); see [Advanced features](advanced_features.md#groups).

## Sub-command union (selection)

The common case: an input where the value is one of several named
sub-commands.

```json
{
  "id": "algorithm",
  "name": "Algorithm",
  "description": "Select processing algorithm.",
  "value-key": "[ALGORITHM]",
  "type": [
    {
      "id": "fast",
      "name": "Fast algorithm",
      "description": "Quick but less accurate.",
      "command-line": "fast [FAST_INPUT] [FAST_OUTPUT]",
      "inputs": [
        { "id": "input",  "name": "Input file",  "type": "File",   "value-key": "[FAST_INPUT]",  "optional": false },
        { "id": "output", "name": "Output file", "type": "String", "value-key": "[FAST_OUTPUT]", "optional": false }
      ],
      "output-files": [
        { "id": "output", "name": "Output", "path-template": "[FAST_OUTPUT]" }
      ]
    },
    {
      "id": "accurate",
      "name": "Accurate algorithm",
      "description": "Slower but more accurate.",
      "command-line": "accurate [ACCURATE_INPUT] [ACCURATE_OUTPUT] [PRECISION]",
      "inputs": [
        { "id": "input",     "name": "Input file",  "type": "File",   "value-key": "[ACCURATE_INPUT]",  "optional": false },
        { "id": "output",    "name": "Output file", "type": "String", "value-key": "[ACCURATE_OUTPUT]", "optional": false },
        {
          "id": "precision", "name": "Precision",
          "type": "Number", "integer": true, "minimum": 1, "maximum": 10,
          "command-line-flag": "-p", "value-key": "[PRECISION]",
          "optional": true, "default-value": 5
        }
      ],
      "output-files": [
        { "id": "output",  "name": "Output",  "path-template": "[ACCURATE_OUTPUT]" },
        { "id": "metrics", "name": "Metrics", "path-template": "[ACCURATE_OUTPUT].metrics.json" }
      ]
    }
  ]
}
```

An invocation must pick exactly one option by its `id`, tagged via the
`@type` discriminator field:

```json
{
  "algorithm": {
    "@type": "accurate",
    "input": "/data/in.nii",
    "output": "out.nii",
    "precision": 8
  }
}
```

The `@type` field at the top of the chosen object is required — that's
how the loader figures out which sub-command's schema to validate
against. The convention matches Styx-generated language bindings, so
invocation dicts are interchangeable between this toolkit and any
Styx-built consumer.

!!! note "Candidate ids must be unique"
    Within a sub-command union, the `id` of each candidate determines
    its `@type` tag. Duplicate ids make the union ambiguous and are
    rejected at descriptor-load time.

## Single sub-command (composite)

When you have a group of parameters that always appear together,
use a single sub-command (an object, not an array):

```json
{
  "id": "config",
  "name": "Configuration",
  "value-key": "[CONFIG]",
  "command-line-flag": "--config",
  "type": {
    "id": "config_options",
    "command-line": "[KEY] [VALUE]",
    "inputs": [
      { "id": "key",   "name": "Key",   "type": "String", "value-key": "[KEY]",   "optional": false },
      { "id": "value", "name": "Value", "type": "String", "value-key": "[VALUE]", "optional": false }
    ]
  },
  "optional": true
}
```

## Repeatable sub-commands

Add `"list": true` to allow the same sub-command structure to appear
multiple times in one invocation:

```json
{
  "id": "transformations",
  "name": "Transformations",
  "value-key": "[TRANSFORMS]",
  "list": true,
  "type": {
    "id": "transform",
    "command-line": "--transform [TYPE] [PARAMETERS]",
    "inputs": [
      {
        "id": "type", "name": "Type",
        "type": "String", "value-key": "[TYPE]",
        "value-choices": ["rotate", "scale", "translate"], "optional": false
      },
      {
        "id": "parameters", "name": "Parameters",
        "type": "Number", "list": true, "value-key": "[PARAMETERS]",
        "optional": false
      }
    ]
  },
  "optional": true
}
```

Resolved with two transforms: `--transform rotate 0 0 90 --transform scale 2 2 1`.

## Nested sub-commands

Sub-commands compose. A sub-command's input can itself have a
sub-command type:

```json
{
  "id": "mode",
  "value-key": "[MODE]",
  "type": [
    {
      "id": "analysis",
      "command-line": "analysis [METHOD]",
      "inputs": [
        {
          "id": "method",
          "value-key": "[METHOD]",
          "type": [
            {
              "id": "parametric",
              "command-line": "parametric [MODEL]",
              "inputs": [
                {
                  "id": "model", "type": "String", "value-key": "[MODEL]",
                  "value-choices": ["linear", "quadratic", "exponential"],
                  "optional": false
                }
              ]
            },
            {
              "id": "nonparametric",
              "command-line": "nonparametric [KERNEL]",
              "inputs": [
                {
                  "id": "kernel", "type": "String", "value-key": "[KERNEL]",
                  "value-choices": ["gaussian", "uniform"], "optional": false
                }
              ]
            }
          ]
        }
      ]
    }
  ]
}
```

## Real-world example: MRtrix3 `5ttgen`

A trimmed version of `5ttgen`'s descriptor — algorithm union over
`freesurfer` and `fsl`, each with its own inputs and outputs:

```json
{
  "schema-version": "0.5+styx",
  "name": "5ttgen",
  "description": "Generate a 5TT image suitable for ACT.",
  "command-line": "5ttgen [ALGORITHM] [OPTIONS]",
  "inputs": [
    {
      "id": "algorithm",
      "name": "algorithm",
      "value-key": "[ALGORITHM]",
      "description": "Select the algorithm to be used.",
      "type": [
        {
          "id": "freesurfer",
          "command-line": "freesurfer [INPUT] [OUTPUT] [LUT_OPT]",
          "inputs": [
            { "id": "input",  "name": "input",  "value-key": "[INPUT]",   "type": "File",   "optional": false },
            { "id": "output", "name": "output", "value-key": "[OUTPUT]",  "type": "String", "optional": false },
            { "id": "lut",    "name": "lut",    "value-key": "[LUT_OPT]", "type": "File",   "optional": true,
              "command-line-flag": "-lut" }
          ],
          "output-files": [
            { "id": "output", "name": "output", "path-template": "[OUTPUT]" }
          ]
        },
        {
          "id": "fsl",
          "command-line": "fsl [INPUT] [OUTPUT] [T2_OPT]",
          "inputs": [
            { "id": "input",  "name": "input",  "value-key": "[INPUT]",  "type": "File",   "optional": false },
            { "id": "output", "name": "output", "value-key": "[OUTPUT]", "type": "String", "optional": false },
            { "id": "t2",     "name": "t2",     "value-key": "[T2_OPT]", "type": "File",   "optional": true,
              "command-line-flag": "-t2" }
          ],
          "output-files": [
            { "id": "output", "name": "output", "path-template": "[OUTPUT]" }
          ]
        }
      ]
    },
    {
      "id": "nocrop", "name": "nocrop", "value-key": "[OPTIONS]",
      "command-line-flag": "-nocrop", "type": "Flag", "optional": true
    }
  ]
}
```

## Best practices

- Prefer sub-commands over `groups` with `mutually-exclusive` when
  options have different parameter sets.
- Keep `id` values unique within each scope (each sub-command body has
  its own input-id namespace, but candidates inside a union must have
  distinct ids).
- Each sub-command can declare its own `output-files`; make sure path
  templates only reference value-keys defined in the same scope.
- Use `list: true` on the parent input for repeatable sub-commands.
- Nest only when the tool's interface genuinely is hierarchical — deep
  nesting is hard to author and reason about.
