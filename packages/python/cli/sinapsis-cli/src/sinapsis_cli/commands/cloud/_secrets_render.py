from rich import print
from rich.table import Table
from sinapsis_contracts.cloud_api.models.secrets.responses import UserSecretListResponse


def print_user_secrets(data: UserSecretListResponse):
    table = Table(title="User Registered Secrets", caption="Secret values not shown")
    table.add_column("Label".title(), style="bold cyan")
    table.add_column("Metadata ID".title(), style="bold cyan")

    # Add rows from the nested list
    for secret in data.secrets:
        table.add_row(secret.label, str(secret.id))

    print(table)
