"""`bosh invocation` and `bosh invocation-schema`.

`bosh invocation` is a drop-in replacement for classic boutiques: it
either validates an invocation against the descriptor (``-i``) or
embeds the generated invocation schema back into the descriptor file
(``-w``). Without flags, it confirms the schema can be built.

`bosh invocation-schema` is the new, pipe-friendly schema dumper —
prints the invocation JSON Schema for a descriptor to stdout, or writes
it to a separate file with ``-o``.
"""

from __future__ import annotations

import json
from pathlib import Path

import typer

from boutiques.invocation import invocation_schema
from boutiques.invocation_check import validate_invocation
from boutiques.loader import DescriptorLoadError, load


def register(app: typer.Typer) -> None:
    @app.command("invocation")
    def invocation(
        descriptor: str = typer.Argument(
            ..., help="Path or http(s) URL to a Boutiques descriptor."
        ),
        invocation_file: Path | None = typer.Option(
            None,
            "--invocation",
            "-i",
            exists=True,
            readable=True,
            help="Validate this invocation against the descriptor's schema.",
        ),
        write_schema: bool = typer.Option(
            False,
            "--write-schema",
            "-w",
            help=(
                "Embed the generated invocation schema into the descriptor file "
                "(under 'invocation-schema'). Requires descriptor to be a local path."
            ),
        ),
    ) -> None:
        """Validate an invocation, or embed the invocation schema in a descriptor.

        Without flags, confirms that an invocation schema can be built for
        the descriptor (a sanity check on the descriptor's input shape).
        With ``-i``, validates the given invocation against that schema.
        With ``-w``, writes the schema back into the descriptor under its
        ``invocation-schema`` field.
        """
        try:
            parsed = load(descriptor)
        except DescriptorLoadError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc

        if invocation_file is not None:
            inv_data = json.loads(invocation_file.read_text())
            errors = validate_invocation(parsed, inv_data)
            if errors:
                for err in errors:
                    typer.echo(str(err), err=True)
                raise typer.Exit(1)
            typer.echo("OK")
            return

        if write_schema:
            descriptor_path = Path(descriptor)
            if not descriptor_path.is_file():
                typer.echo(
                    "--write-schema requires the descriptor to be a local file path.",
                    err=True,
                )
                raise typer.Exit(1)
            schema = invocation_schema(parsed)
            data = json.loads(descriptor_path.read_text())
            data["invocation-schema"] = schema
            descriptor_path.write_text(json.dumps(data, indent=2) + "\n")
            typer.echo(f"Wrote invocation-schema into {descriptor_path}")
            return

        # Plain mode: confirm the schema can be built.
        invocation_schema(parsed)
        typer.echo("OK")

    @app.command("invocation-schema")
    def invocation_schema_cmd(
        descriptor: str = typer.Argument(
            ..., help="Path or http(s) URL to a Boutiques descriptor."
        ),
        output: Path | None = typer.Option(
            None,
            "--output",
            "-o",
            help="File to write the schema into. Without -o, prints to stdout.",
        ),
    ) -> None:
        """Emit the JSON Schema describing valid invocations for a descriptor.

        The schema is derived from the descriptor's inputs and reflects
        everything ``bosh exec simulate`` / ``launch`` enforces structurally:
        required fields, types, value-choices, numeric ranges, list bounds,
        and sub-command unions.
        """
        try:
            parsed = load(descriptor)
        except DescriptorLoadError as exc:
            typer.echo(str(exc), err=True)
            raise typer.Exit(1) from exc

        schema = invocation_schema(parsed)
        rendered = json.dumps(schema, indent=2)

        if output is None:
            typer.echo(rendered)
            return

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered + "\n")
        typer.echo(f"Wrote {output}", err=True)
