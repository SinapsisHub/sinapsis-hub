from dataclasses import dataclass

from .base import BaseApiPaths


@dataclass(frozen=True)
class _ApiHealthPaths:
    base: str = f"{BaseApiPaths.base}/health"


API_HEALTH_PATHS = _ApiHealthPaths()
