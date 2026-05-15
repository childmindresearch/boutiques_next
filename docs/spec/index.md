# Specification

The Boutiques specification defines a JSON format for describing
command-line tools — their inputs, outputs, container images, and the
rules that govern how an invocation translates into a runnable command.

This section is the canonical, human-readable reference. The
machine-readable JSON Schema lives under
[`/schema/0.5/`](../schema/0.5/descriptor.schema.json) and
[`/schema/0.5+styx/`](../schema/0.5+styx/descriptor.schema.json).

!!! note "Work in progress"
    The narrative spec pages are being ported from the styxbook guide
    with framing updated for this repository as the canonical home.
    Until that pass lands, please refer to:

    - The JSON Schema artifacts linked above.
    - The Pydantic models under `boutiques.models.v05` and
      `boutiques.models.v05_styx` — these are the source of truth from
      which the JSON Schema is generated.
    - The original [styxbook Boutiques guide](https://github.com/styx-api/styxbook/tree/master/src/boutiques_guide),
      which covers the same shape (verbatim port pending).

## Schema versions

| Version | Notes |
| --- | --- |
| `0.5` | The original Boutiques specification. |
| `0.5+styx` | Strict superset of 0.5: adds sub-command hierarchy and alternation as new input shapes; adds `mutable` + `resolve-parent` on File inputs; makes `tool-version` optional to accommodate descriptor-registry workflows that carry version metadata in sidecar packaging. |

Every valid `0.5` descriptor is a valid `0.5+styx` descriptor; only the
`schema-version` literal needs to change.
