"""Discover templates and packages through the existing documentation catalog.

For structured management-only filters use ``search_registry``; display/search
operations reuse the permission-filtered docs catalog API.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sinapsis_contracts.cloud_api.paths.docs import DOCS_PATHS

from sinapsis_sdk.common.base_resource_client import BaseClientResource


class CatalogPage(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    total: int = 0
    limit: int = 50
    offset: int = 0


class TemplatesResource(BaseClientResource):
    """User-visible template documentation search, backed by management's DB."""

    def __init__(self, http) -> None:
        super().__init__(http, DOCS_PATHS.base)

    async def list(
        self,
        *,
        q: str | None = None,
        category: str | None = None,
        package: str | None = None,
        tag: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> CatalogPage:
        params = {
            key: value
            for key, value in {
                "q": q,
                "category": category,
                "package": package,
                "tag": tag,
                "limit": limit,
                "offset": offset,
            }.items()
            if value is not None
        }
        data = await self._http.get(self._path(DOCS_PATHS.templates, release="latest"), params=params)
        return CatalogPage.model_validate(data)

    async def search(self, query: str, **filters: Any) -> CatalogPage:
        """Relevance-ranked search over class names, tags, description and capabilities."""
        return await self.list(q=query, **filters)

    async def get(self, template_id: str | UUID) -> dict[str, Any]:
        return await self._http.get(self._path(DOCS_PATHS.template, release="latest", template_id=str(template_id)))

    async def list_all(self, *, limit: int = 50, offset: int = 0) -> CatalogPage:
        return await self.list(limit=limit, offset=offset)

    async def packages(self, *, limit: int = 50, offset: int = 0) -> CatalogPage:
        data = await self._http.get(
            self._path(DOCS_PATHS.packages, release="latest"), params={"limit": limit, "offset": offset}
        )
        return CatalogPage.model_validate(data)

    async def search_registry(self, filters: dict[str, Any], *, limit: int = 50, offset: int = 0) -> dict[str, Any]:
        """Run management's typed capability/name/schema filters as the current user."""
        from sinapsis_contracts.common.paths import BaseApiPaths

        return await self._http.post(
            f"{BaseApiPaths.base}/management/templates/search", json=filters, params={"limit": limit, "offset": offset}
        )
