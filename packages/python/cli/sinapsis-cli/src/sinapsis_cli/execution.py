"""Execution context shared by profile-aware CLI commands."""

from dataclasses import dataclass

import typer
from sinapsis_sdk.cloud_api._config import ConfigStore
from sinapsis_sdk.cloud_api._credentials import create_credential_store
from sinapsis_sdk.cloud_api.client import CloudSinapsisAPIClient
from sinapsis_sdk.cloud_api.cloud_config import CloudAPIConfig
from sinapsis_sdk.common.base_config import BaseAPIConfig
from sinapsis_sdk.local_api.client import SinapsisAPIClient

from sinapsis_cli.config import ExecutionBackend, Profile


@dataclass(frozen=True)
class ExecutionContext:
    """Resolved execution environment for one CLI invocation."""

    profile: Profile
    explicit_profile: bool = False

    @property
    def profile_name(self) -> str:
        """Return the selected profile name."""
        return self.profile.name

    @property
    def api_url(self) -> str:
        """Return the profile API URL.

        Raises:
            ValueError: If the selected profile is not API-backed.
        """
        if self.profile.api_url is None:
            raise ValueError(f"Profile {self.profile.name!r} does not define an API URL.")

        return self.profile.api_url


def get_execution_context(context: typer.Context) -> ExecutionContext:
    """Return the execution context attached to a Typer command."""
    if isinstance(context.obj, ExecutionContext):
        return context.obj

    raise RuntimeError("Sinapsis execution context was not initialized.")


def build_api_config(execution: ExecutionContext, *, api_url: str | None = None) -> CloudAPIConfig:
    """Build an SDK API configuration for the selected profile.

    The profile owns the API endpoint; timeout comes from ``ConfigStore``.
    Supabase configuration remains readable for legacy settings only.
    """
    current = ConfigStore().load()
    target_url = (api_url or execution.api_url).rstrip("/")

    return CloudAPIConfig(api_url=target_url, timeout=current.timeout)


def create_api_client(
    execution: ExecutionContext, *, api_url: str | None = None
) -> CloudSinapsisAPIClient | SinapsisAPIClient:
    """Create the appropriate SDK client for the selected profile."""
    if execution.profile.backend == ExecutionBackend.LOCAL_API:
        return SinapsisAPIClient(config=BaseAPIConfig(api_url=(api_url or execution.api_url).rstrip("/")))

    if execution.profile.backend == ExecutionBackend.CLOUD:
        return CloudSinapsisAPIClient(
            config=build_api_config(execution, api_url=api_url),
            credential_store=create_credential_store(),
        )

    raise ValueError(f"Unsupported profile type: {execution.profile.type!r}")


__all__ = ["ExecutionContext", "build_api_config", "create_api_client", "get_execution_context"]
