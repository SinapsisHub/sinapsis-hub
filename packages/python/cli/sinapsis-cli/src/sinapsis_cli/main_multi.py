"""Alternative Sinapsis CLI entry point with optional full-color output."""

import sys

import typer.rich_utils
from rich.console import Console
from rich.text import Text
from rich.theme import Theme

from sinapsis_cli.main import create_app, resolve_invocation

neo_theme = Theme(
    {
        "panel.title": "bold #00F5FF",
        "command": "bold #00FFCC",
        "option": "bold #FF79C6",
        "brand": "bold #FF007F",
        "accent": "bold #00F5FF",
        "muted": "#6272A4",
    }
)

plain_console = Console()
color_console = Console(theme=neo_theme, style="on #1E1B4B")
from rich.console import Console

console = Console()


LOGO = [
    "                                                 XXXX",
    "                                               XXXXXX",
    "                                          XXXX    XXX",
    "   XXXXXXXXXXX              XXXXXXXXXXX           XXX",
    "    XXXXXXXXXXXX          XXXXXXXXXXXX            XXX",
    "       XXXXXXXXXXX      XXXXXXXXXXX               XXX",
    "         XXXXXXXXXXX  XXXXXXXXXXX",
    "           XXXXXXXXXXXXXXXXXXXX",
    "             XXXXXXXXXXXXXXXX",
    "               XXXXXXXXXXXX",
    "             XXXXXXXXXXXXXXXX",
    "           XXXXXXXXXXXXXXXXXXXX",
    "         XXXXXXXXXXXXXXXXXXXXXXXX",
    "       XXXXXXXXXXXX    XXXXXXXXXXXX",
    "     XXXXXXXXXXXX        XXXXXXXXXXXX",
    "   XXXXXXXXXXX              XXXXXXXXXXX",
]


# sinapsis brand gradient:
# cyan → blue → indigo → violet → purple
GRADIENT = [
    (0.00, "#38B6FF"),
    (0.25, "#3978F6"),
    (0.50, "#4650E8"),
    (0.75, "#7248E8"),
    (1.00, "#A855F7"),
]


def _hex_to_rgb(color: str) -> tuple[int, int, int]:
    """Convert a hex color to an RGB tuple."""
    color = color.lstrip("#")

    return tuple(int(color[i : i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert an RGB tuple to a hex color."""
    return "#{:02x}{:02x}{:02x}".format(*rgb)


def _interpolate_color(start: str, end: str, amount: float) -> str:
    """Interpolate between two hex colors."""
    start_rgb = _hex_to_rgb(start)
    end_rgb = _hex_to_rgb(end)

    rgb = tuple(
        round(start_value + (end_value - start_value) * amount) for start_value, end_value in zip(start_rgb, end_rgb)
    )

    return _rgb_to_hex(rgb)


def _gradient_color(position: float) -> str:
    """Return a color from the sinapsis gradient at position 0.0–1.0."""
    position = max(0.0, min(1.0, position))

    for index in range(len(GRADIENT) - 1):
        start_position, start_color = GRADIENT[index]
        end_position, end_color = GRADIENT[index + 1]

        if start_position <= position <= end_position:
            amount = (position - start_position) / (end_position - start_position)

            return _interpolate_color(start_color, end_color, amount)

    return GRADIENT[-1][1]


def print_logo(console: Console) -> None:
    """Print the sinapsis logo using the brand gradient."""
    text = Text()

    width = max(len(row) for row in LOGO)
    height = len(LOGO)

    for y, row in enumerate(LOGO):
        for x, character in enumerate(row):
            if character != "X":
                text.append(" ")
                continue

            # Normalize the block's position within the logo.
            x_position = x / max(width - 1, 1)
            y_position = y / max(height - 1, 1)

            # Diagonal gradient:
            #
            # cyan / blue
            #       ↘
            #         indigo
            #              ↘
            #                violet / purple
            #
            position = (x_position + y_position) / 2

            text.append("█", style=_gradient_color(position))

        text.append("\n")

    console.print(text, crop=False)


def main() -> None:
    """Run the profile-aware CLI with optional ``--color`` presentation."""
    arguments = list(sys.argv[1:])
    use_color = "--color" in arguments

    if use_color:
        arguments = [argument for argument in arguments if argument != "--color"]
        typer.rich_utils._get_rich_console = lambda *args, **kwargs: color_console
        print_logo(color_console)
    else:
        typer.rich_utils._get_rich_console = lambda *args, **kwargs: plain_console

    execution, remaining = resolve_invocation(arguments)
    create_app(execution)(args=remaining, prog_name="sinapsis")


if __name__ == "__main__":
    main()
