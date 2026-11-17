from dataclasses import dataclass

from sinapsis_contracts.common.paths import BaseApiPaths


@dataclass(frozen=True)
class SecretPaths:
    base: str = f"{BaseApiPaths.base}/user-secrets"
    create: str = "/create"
    list: str = "/list"
    delete: str = "/{metadata_id}"
    get: str = "/{metadata_id}"


USER_SECRET_PATHS = SecretPaths()
