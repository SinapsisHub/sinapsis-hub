import inspect

import sinapsis.templates as templates
import typer
import yaml
from rich.console import Console
from rich.syntax import Syntax
from sinapsis.cli import (
    get_template,
    make_example_template_config,
    parse_attributes_base_model,
    parse_template_doc_string,
)
from sinapsis.template import Template

from sinapsis_cli.shared.terminal import divider

console = Console()


def print_config(template_name: str, output: str = "yaml") -> None:
    config_dict = make_example_template_config(template_name, templates)
    if output == "json":
        console.print_json(data=config_dict)

    elif output == "yaml":
        yaml_text = yaml.safe_dump(config_dict, sort_keys=False)
        console.print(Syntax(yaml_text, "yaml", theme="ansi_dark", line_numbers=False))
    else:
        console.print(config_dict)


def display_single_template_info(template_name: str) -> None:
    template_cls: Template = get_template(template_name, templates)
    if template_cls:
        typer.echo(inspect.getfile(template_cls))
        typer.echo(parse_template_doc_string(template_name, template_cls))
        typer.echo(f"\n{template_name} attributes: ")
        for att_line in parse_attributes_base_model(template_cls.AttributesBaseModel):
            typer.echo(att_line)
        divider(0)


def display_all(names_only):
    if names_only:
        divider(0)
        typer.echo("All templates available:")
        for template_name in templates.__all__:
            typer.echo(f"    {template_name}")
        raise typer.Exit(code=1)

    for template_name in templates.__all__:
        try:
            display_single_template_info(template_name)
        except (ModuleNotFoundError, ImportError) as err:
            typer.echo(f"Unable to import {template_name} due to", err=err)
