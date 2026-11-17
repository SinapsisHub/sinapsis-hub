from docker.models.containers import Container

import docker

from .base import DockerRuntimeError, ServiceStatus
from .services import get_runtime


def ensure_services(client: docker.DockerClient | None = None, *, rebuild_image: bool = False) -> dict[str, Container]:
    """Ensure the Sinapsis router and API are running and healthy."""
    return get_runtime().ensure(client, rebuild_image=rebuild_image)


def stop_services(client: docker.DockerClient | None = None) -> None:
    """Stop the Sinapsis router and API."""
    get_runtime().stop(client)


def restart_services(client: docker.DockerClient | None = None) -> dict[str, Container]:
    """Restart the Sinapsis router and API and wait until ready."""
    return get_runtime().restart(client)


def remove_services(client: docker.DockerClient | None = None, *, remove_network: bool = False) -> None:
    """Remove Sinapsis containers and optionally their network."""
    get_runtime().remove(client, remove_network=remove_network)


def get_service_status(client: docker.DockerClient | None = None) -> dict[str, ServiceStatus]:
    """Return the current state of the Sinapsis runtime services."""
    return get_runtime().status(client)


__all__ = [
    "DockerRuntimeError",
    "ServiceStatus",
    "ensure_services",
    "get_service_status",
    "remove_services",
    "restart_services",
    "stop_services",
]
