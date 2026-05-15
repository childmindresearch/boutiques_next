"""Render a Boutiques descriptor as a human-readable tree.

The output uses :mod:`rich` for colour, but degrades gracefully when
stdout is not a terminal (rich detects that and skips ANSI codes).
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.tree import Tree

from boutiques.loader import AnyDescriptor
from boutiques.models.v05.containers import DockerOrSingularityImage, RootfsImage
from boutiques.models.v05.inputs import FileInput, FlagInput, NumberInput, StringInput
from boutiques.models.v05_styx.inputs import (
    SubCommandInput,
    SubCommandType,
    SubCommandUnionInput,
)


def pprint(descriptor: AnyDescriptor, *, console: Console | None = None) -> None:
    """Print a tree view of ``descriptor`` to the console."""
    (console or Console()).print(build_tree(descriptor))


def build_tree(descriptor: AnyDescriptor) -> Tree:
    """Return the :class:`rich.tree.Tree` representing a descriptor."""
    tree = Tree(_descriptor_header(descriptor))

    tree.add(f"[cyan]command-line[/cyan]: [yellow]{descriptor.command_line}[/yellow]")

    if descriptor.container_image is not None:
        tree.add(_container_summary(descriptor.container_image))

    _add_inputs(tree, descriptor.inputs, label="inputs")

    if descriptor.output_files:
        _add_outputs(tree, descriptor.output_files)

    if descriptor.groups:
        groups_node = tree.add(f"[cyan]groups[/cyan] ({len(descriptor.groups)})")
        for group in descriptor.groups:
            flags = []
            if group.mutually_exclusive:
                flags.append("mutually-exclusive")
            if group.one_is_required:
                flags.append("one-is-required")
            if group.all_or_none:
                flags.append("all-or-none")
            flag_text = f" [dim]({', '.join(flags)})[/dim]" if flags else ""
            members = ", ".join(group.members)
            groups_node.add(f"[bold]{group.id}[/bold]{flag_text}: {members}")

    if descriptor.environment_variables:
        env_node = tree.add(
            f"[cyan]environment-variables[/cyan] ({len(descriptor.environment_variables)})"
        )
        for var in descriptor.environment_variables:
            env_node.add(f"{var.name}=[yellow]{var.value}[/yellow]")

    if descriptor.error_codes:
        codes_node = tree.add(f"[cyan]error-codes[/cyan] ({len(descriptor.error_codes)})")
        for ec in descriptor.error_codes:
            codes_node.add(f"{ec.code}: [dim]{ec.description}[/dim]")

    if descriptor.tests:
        tests_node = tree.add(f"[cyan]tests[/cyan] ({len(descriptor.tests)})")
        for t in descriptor.tests:
            tests_node.add(t.name)

    _add_stdio_output(tree, "stdout-output", getattr(descriptor, "stdout_output", None))
    _add_stdio_output(tree, "stderr-output", getattr(descriptor, "stderr_output", None))

    return tree


# ---------------------------------------------------------------------------
# Header / containers
# ---------------------------------------------------------------------------


def _descriptor_header(descriptor: AnyDescriptor) -> str:
    version = descriptor.tool_version or "—"
    parts = [f"[bold]{descriptor.name}[/bold] [dim]v{version}[/dim]"]
    parts.append(f"[dim]({descriptor.schema_version})[/dim]")
    header = " ".join(parts)
    if descriptor.description:
        header += f"\n[italic]{descriptor.description}[/italic]"
    return header


def _container_summary(image: Any) -> str:
    if isinstance(image, DockerOrSingularityImage):
        index = f"{image.index}/" if image.index else ""
        return f"[cyan]container[/cyan]: [magenta]{image.type}[/magenta] {index}{image.image}"
    if isinstance(image, RootfsImage):
        return f"[cyan]container[/cyan]: [magenta]rootfs[/magenta] {image.url}"
    return f"[cyan]container[/cyan]: {image}"


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------


def _add_inputs(parent: Tree, inputs: list[Any] | None, *, label: str) -> None:
    inputs = inputs or []
    node = parent.add(f"[cyan]{label}[/cyan] ({len(inputs)})")
    for inp in inputs:
        _add_input(node, inp)


def _add_input(parent: Tree, inp: Any) -> None:
    type_str = _input_type_label(inp)
    requiredness = "optional" if inp.optional else "required"
    pieces = [f"[bold]{inp.id}[/bold] [dim]({type_str}, {requiredness})[/dim]"]
    if getattr(inp, "command_line_flag", None):
        pieces.append(f"[yellow]{inp.command_line_flag}[/yellow]")
    if inp.value_key:
        pieces.append(f"[dim]{inp.value_key}[/dim]")
    node = parent.add(" ".join(pieces))

    if inp.description:
        node.add(f"[italic]{inp.description}[/italic]")

    if getattr(inp, "default_value", None) is not None:
        node.add(f"default: {inp.default_value!r}")

    if isinstance(inp, NumberInput):
        if inp.minimum is not None or inp.maximum is not None:
            lo = "-inf" if inp.minimum is None else str(inp.minimum)
            hi = "+inf" if inp.maximum is None else str(inp.maximum)
            lb = "(" if inp.exclusive_minimum else "["
            rb = ")" if inp.exclusive_maximum else "]"
            node.add(f"range: {lb}{lo}, {hi}{rb}")

    if getattr(inp, "value_choices", None):
        node.add(f"choices: {inp.value_choices}")

    if getattr(inp, "list_", None):
        lo = inp.min_list_entries if inp.min_list_entries is not None else "0"
        hi = inp.max_list_entries if inp.max_list_entries is not None else "inf"
        sep = inp.list_separator if inp.list_separator is not None else "space"
        node.add(f"list: {lo}-{hi} entries, separator={sep!r}")

    if getattr(inp, "requires_inputs", None):
        node.add(f"requires: {inp.requires_inputs}")
    if getattr(inp, "disables_inputs", None):
        node.add(f"disables: {inp.disables_inputs}")

    if isinstance(inp, SubCommandInput):
        _add_subcommand_body(node, inp.type)
    elif isinstance(inp, SubCommandUnionInput):
        for sc in inp.type:
            sc_node = node.add(f"[bold magenta]{sc.id}[/bold magenta]")
            _add_subcommand_body(sc_node, sc)


def _input_type_label(inp: Any) -> str:
    if isinstance(inp, FlagInput):
        return "Flag"
    if isinstance(inp, StringInput):
        return "String"
    if isinstance(inp, FileInput):
        return "File"
    if isinstance(inp, NumberInput):
        return "Number (int)" if inp.integer else "Number"
    if isinstance(inp, SubCommandInput):
        return "SubCommand"
    if isinstance(inp, SubCommandUnionInput):
        return f"SubCommandUnion[{len(inp.type)}]"
    return type(inp).__name__


def _add_subcommand_body(parent: Tree, sub: SubCommandType) -> None:
    parent.add(f"[cyan]command-line[/cyan]: [yellow]{sub.command_line}[/yellow]")
    _add_inputs(parent, sub.inputs, label="inputs")
    if sub.output_files:
        _add_outputs(parent, sub.output_files)


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------


def _add_outputs(parent: Tree, outputs: list[Any]) -> None:
    node = parent.add(f"[cyan]output-files[/cyan] ({len(outputs)})")
    for output in outputs:
        requiredness = "optional" if output.optional else "required"
        line = f"[bold]{output.id}[/bold] [dim]({requiredness})[/dim]"
        if output.path_template:
            line += f"  [green]{output.path_template}[/green]"
        elif output.conditional_path_template:
            line += "  [green](conditional)[/green]"
        sub = node.add(line)
        if output.description:
            sub.add(f"[italic]{output.description}[/italic]")
        if output.path_template_stripped_extensions:
            sub.add(f"strip-exts: {output.path_template_stripped_extensions}")


def _add_stdio_output(tree: Tree, label: str, decl: Any | None) -> None:
    if decl is None:
        return
    line = f"[cyan]{label}[/cyan]: [bold]{decl.id}[/bold]"
    if decl.name:
        line += f"  [italic]{decl.name}[/italic]"
    tree.add(line)


__all__ = ["build_tree", "pprint"]
