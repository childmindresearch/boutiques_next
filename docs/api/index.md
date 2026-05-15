# Python API

!!! note "Not yet auto-generated"
    A full `mkdocstrings`-driven API reference is on the roadmap. Until
    it lands, the public Python surface is:

    - `boutiques.load(source)` — parse from path / URL / dict / JSON string.
    - `boutiques.validate.validate(source)` → `ValidationResult`.
    - `boutiques.example.generate(descriptor, complete=False)` → `dict`.
    - `boutiques.execution.simulate(descriptor, invocation)` → `str`.
    - `boutiques.execution.launch(descriptor, invocation, runtime=..., ...)` → `LaunchResult`.
    - `boutiques.invocation.invocation_model_for(descriptor)` → `type[BaseModel]`.
    - `boutiques.schema_export.{schema_for, export_all}` for JSON Schema artifacts.

    The CLI delegates one-to-one to these functions; see each CLI page
    for the Python equivalent.
