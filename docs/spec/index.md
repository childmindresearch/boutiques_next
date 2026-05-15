# Specification

A Boutiques descriptor is a JSON file describing a command-line tool —
its inputs and outputs, container image, and the rules governing how an
invocation is translated into a runnable command.

This section is the canonical, human-readable reference. The
machine-readable JSON Schema lives under
[`/schema/0.5/`](../schema/0.5/descriptor.schema.json) and
[`/schema/0.5+styx/`](../schema/0.5+styx/descriptor.schema.json).

## How to read this section

- **[Basic structure](basic_structure.md)** — top-level fields, the four
  input types, command-line formation, output files.
- **[File handling](file_handling.md)** — input/output file inputs,
  path templates, extension handling.
- **[Subcommands](subcommands.md)** — sub-command hierarchy and
  alternation (the styx extensions).
- **[Advanced features](advanced_features.md)** — groups, container
  configurations, value constraints, list and flag separators.
- **[Examples](examples.md)** — fully worked descriptors.
- **[Troubleshooting](troubleshooting.md)** — common authoring mistakes.

## Schema versions

| Version | Notes |
| --- | --- |
| `0.5` | The original Boutiques specification. |
| `0.5+styx` | Strict superset of 0.5 adding sub-command inputs (hierarchy + alternation) and a couple of File-input attributes (`mutable`, `resolve-parent`). Makes `tool-version` optional so descriptor-registry workflows can carry version metadata in sidecar packaging. |

Every valid `0.5` descriptor is also a valid `0.5+styx` descriptor;
only the `schema-version` literal needs to change.

## Quick example

```json
{
  "schema-version": "0.5+styx",
  "name": "example_tool",
  "description": "An example tool",
  "tool-version": "1.0.0",
  "command-line": "example_tool [INPUT] [OUTPUT] [VERBOSE]",
  "inputs": [
    {
      "id": "input_file",
      "name": "Input file",
      "type": "File",
      "value-key": "[INPUT]",
      "optional": false
    },
    {
      "id": "output_file",
      "name": "Output file",
      "type": "String",
      "value-key": "[OUTPUT]",
      "optional": false
    },
    {
      "id": "verbose",
      "name": "Verbose output",
      "type": "Flag",
      "command-line-flag": "-v",
      "value-key": "[VERBOSE]",
      "optional": true
    }
  ],
  "output-files": [
    {
      "id": "output",
      "name": "Output file",
      "path-template": "[OUTPUT]"
    }
  ]
}
```
