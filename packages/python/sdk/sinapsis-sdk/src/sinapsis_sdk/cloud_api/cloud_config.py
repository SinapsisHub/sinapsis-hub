"""Configuration for the Sinapsis SDK cloud API."""

from dataclasses import dataclass

from sinapsis_sdk.common.base_config import BaseAPIConfig
from sinapsis_sdk.env_vars import SINAPSIS_CLOUD_API_URL


@dataclass(frozen=True, slots=True)
class CloudAPIConfig(BaseAPIConfig):
    """Cloud API options; Supabase credentials belong to their clients, not the SDK."""

    api_url: str = SINAPSIS_CLOUD_API_URL
