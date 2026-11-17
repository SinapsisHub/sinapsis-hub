from dataclasses import dataclass

from sinapsis_contracts.common.paths import BaseApiPaths


@dataclass(frozen=True)
class WebhookPaths:
    base: str = f"{BaseApiPaths.base}/webhook_integrations"

    register: str = "/register"
    list: str = "/list"
    delete: str = "/{webhook_id}"
    toggle: str = "/{webhook_id}"


@dataclass(frozen=True)
class PublicWebhookPaths:
    base: str = f"{BaseApiPaths.base}/public/webhooks"

    webhook: str = "/{webhook_id}"


WEBHOOK_PATHS = WebhookPaths()
PUBLIC_WEBHOOK_PATHS = PublicWebhookPaths()
