"""Pydantic descriptor models.

Two sibling schemas live here:

- ``v05``: the original Boutiques 0.5 specification.
- ``v05_styx``: a strict superset of 0.5 adding the Styx extensions
  (SubCommand hierarchy, SubCommandUnion alternation).

Every v05 descriptor is a valid v05_styx descriptor modulo the
``schema-version`` field.
"""
