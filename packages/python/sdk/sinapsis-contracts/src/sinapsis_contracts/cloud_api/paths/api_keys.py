from dataclasses import dataclass

from sinapsis_contracts.common.paths import BaseApiPaths


@dataclass(frozen=True)
class ApiAccessKeyPaths:
    base: str = f"{BaseApiPaths.base}/api-keys"
    create: str = "/create"
    delete: str = "/delete"
    list: str = "/list"
    validate: str = "/validate"
    fetch: str = "/fetch"


ACCESS_API_KEY_PATHS = ApiAccessKeyPaths()
