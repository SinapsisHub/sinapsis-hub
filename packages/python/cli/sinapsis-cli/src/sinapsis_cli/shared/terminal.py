import shutil

import typer


def divider(width: int = 40) -> None:
    width = width or shutil.get_terminal_size().columns
    typer.echo("─" * width)
