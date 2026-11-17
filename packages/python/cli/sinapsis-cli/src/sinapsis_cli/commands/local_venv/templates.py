"""Local template inspection commands."""

from enum import Enum

import typer

from ._templates_render import display_all, display_single_template_info, print_config

app = typer.Typer(
    name="templates",
    help="Inspect templates available in the local environment.",
    no_args_is_help=True,
)


class OutputFormat(str, Enum):
    """Supported template configuration output formats."""

    PRETTY = "pretty"
    JSON = "json"
    YAML = "yaml"


@app.command()
def docstring(template_name: str = typer.Argument(..., help="The name of the template.")) -> None:
    """Show the docstring for a locally installed template."""
    display_single_template_info(template_name)


@app.command("show-all")
def all_names(
    names_only: bool = typer.Option(False, "--names-only", help="Show only template names."),
) -> None:
    """Show locally installed templates."""
    display_all(names_only)


@app.command("example-config")
def example_config(
    template_name: str = typer.Argument(..., help="The name of the template."),
    output: OutputFormat = typer.Option(
        OutputFormat.YAML, "--output", "-o", help="Output format: pretty, json, or yaml."
    ),
) -> None:
    """Print an example configuration for a local template."""
    print_config(template_name, output)
    typer.echo()
