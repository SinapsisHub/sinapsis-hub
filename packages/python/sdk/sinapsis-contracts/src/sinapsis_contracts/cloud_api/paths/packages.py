"""Canonical Cloud package-index, publishing and analytics route paths.

These constants describe HTTP endpoints, not Python package-index hosts.
The latter are deployment configuration and must remain independently verified.
"""

from dataclasses import dataclass

from sinapsis_contracts.common.paths import BaseApiPaths


@dataclass(frozen=True, slots=True)
class PackagePaths:
    """Cloud package route prefixes and method-specific relative paths."""

    base: str = f"{BaseApiPaths.base}/packages"
    index: str = "/index"
    index_public: str = "/index/public"
    releases: str = "/releases"
    public: str = "/public"
    internal_analytics: str = f"{BaseApiPaths.base}/internal/package-analytics"
    list: str = "/list"
    artifact: str = "/artifact"
    preflight: str = "/preflight"
    publish: str = "/publish"
    artifacts_commit: str = "/artifacts/commit"
    analytics: str = "/{distribution}/analytics"
    deliveries: str = "/deliveries"

    @property
    def index_list(self) -> str:
        """Authenticated index discovery/metadata endpoint."""
        return f"{self.base}{self.index}{self.list}"

    @property
    def index_artifact(self) -> str:
        """Authenticated index artifact-authorization endpoint."""
        return f"{self.base}{self.index}{self.artifact}"

    @property
    def public_index_list(self) -> str:
        """Anonymous index discovery/metadata endpoint."""
        return f"{self.base}{self.index_public}{self.list}"

    @property
    def public_index_artifact(self) -> str:
        """Anonymous index artifact-authorization endpoint."""
        return f"{self.base}{self.index_public}{self.artifact}"

    @property
    def analytics_ingest(self) -> str:
        """Service-authenticated AWS delivery-ingestion endpoint."""
        return f"{self.internal_analytics}{self.deliveries}"


PACKAGE_PATHS = PackagePaths()
