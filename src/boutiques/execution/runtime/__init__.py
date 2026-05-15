"""Container/local runtime backends.

Each backend exposes a ``run`` callable that takes a resolved command-line
plus bind-mount specs and returns a result. Selection is by name:
``local``, ``docker``, ``singularity``.
"""
