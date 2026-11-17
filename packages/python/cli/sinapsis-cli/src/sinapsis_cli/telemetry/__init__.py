"""Opt-in, privacy-scoped local CLI telemetry."""

from sinapsis_cli.telemetry.core import (
    record_cli_invocation, record_inventory_if_due,
)

__all__ = ["record_cli_invocation", "record_inventory_if_due"]
