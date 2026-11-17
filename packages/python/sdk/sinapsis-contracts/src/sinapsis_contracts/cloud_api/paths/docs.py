"""Canonical documentation API paths shared by FastAPI and client contracts."""

from dataclasses import dataclass

from sinapsis_contracts.common.paths import BaseApiPaths


@dataclass(frozen=True, slots=True)
class DocsPaths:
    """Relative paths are appended to ``base`` by FastAPI's router."""

    base: str = f"{BaseApiPaths.base}/documentation"
    articles: str = "/releases/{release}/articles"
    article: str = "/releases/{release}/articles/{slug:path}"
    navigation: str = "/releases/{release}/navigation"
    templates: str = "/releases/{release}/templates"
    template: str = "/releases/{release}/templates/{template_id:path}"
    packages: str = "/releases/{release}/packages"
    search: str = "/releases/{release}/search"
    openapi: str = "/releases/{release}/rest-api/openapi"
    media: str = "/releases/{release}/media/{digest}"
    publish_latest: str = "/publications/sync"


DOCS_PATHS = DocsPaths()


@dataclass(frozen=True, slots=True)
class DocsHeaders:
    """Trusted publishing event header names, shared by client and API."""

    publication_timestamp: str = "X-Sinapsis-Timestamp"
    publication_event_id: str = "X-Sinapsis-Event-Id"
    publication_signature: str = "X-Sinapsis-Signature"


DOCS_HEADERS = DocsHeaders()
