"""Configuration for the Sinapsis SDK."""

from dataclasses import dataclass

from sinapsis_sdk.env_vars import SINAPSIS_LOCAL_API_URL

_DEFAULT_TIMEOUT = 30.0


@dataclass(frozen=True, slots=True)
class BaseAPIConfig:
    """Configuration for the Sinapsis SDK.

    Args:
        api_url: Base URL of the Sinapsis API.

        timeout: HTTP request timeout in seconds.
    """

    api_url: str = SINAPSIS_LOCAL_API_URL
    timeout: float = _DEFAULT_TIMEOUT
