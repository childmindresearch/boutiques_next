"""Pydantic descriptor models.

Two sibling schemas live here:

- ``v_0_5``: the original Boutiques 0.5 specification.
- ``v_styx_1``: a strict superset of 0.5 adding the Styx extensions
  (List inputs, SubCommand hierarchy, SubCommandUnion alternation).

Every v_0_5 descriptor is a valid v_styx_1 descriptor modulo the
``schema-version`` field.
"""
