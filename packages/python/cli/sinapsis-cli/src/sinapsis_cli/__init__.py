"""Sinapsis CLI package."""

__all__ = ["app"]


def __getattr__(name: str):
    """Lazily expose the default Typer application for compatibility."""
    if name == "app":
        from .main import app

        return app

    raise AttributeError(name)
