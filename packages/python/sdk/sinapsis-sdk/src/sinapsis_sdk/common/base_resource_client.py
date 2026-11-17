from sinapsis_contracts.common.paths import BaseApiPaths

from sinapsis_sdk.common.async_http_client import AsyncHTTPClient


class BaseClientResource:
    def __init__(self, http: AsyncHTTPClient, base_path: str) -> None:
        self._http = http
        self._base = base_path

    def _path(self, template: str, **params: str) -> str:
        return BaseApiPaths.render(template, base=self._base, **params)
