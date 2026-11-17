"""Render user-owned webhook integrations."""

from rich import print
from rich.table import Table


def print_webhooks(data) -> None:
    table = Table(title="Webhook Integrations", caption=f"Total: {len(data.items)}")
    for heading in ("ID", "Name", "Provider", "Active", "Public URL"):
        table.add_column(heading)
    for item in data.items:
        table.add_row(
            str(item.webhook_id),
            item.integration_name,
            item.provider,
            str(item.is_active),
            item.webhook_url,
        )
    print(table)
