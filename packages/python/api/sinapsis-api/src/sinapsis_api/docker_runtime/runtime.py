from collections.abc import Sequence
from dataclasses import dataclass

from docker.models.containers import Container

import docker

from .base import (
    ContainerSpec,
    DockerRuntimeError,
    ServiceStatus,
    ensure_container,
    ensure_network,
    get_container,
    get_container_health,
    get_docker_client,
    remove_container,
    stop_container,
    wait_for_ready,
)
from .image import ImageSpec, ensure_image


@dataclass(frozen=True, slots=True)
class DockerRuntime:
    """Manage an ordered collection of Docker services.

    Services are started in declaration order and stopped in reverse order,
    allowing dependencies to be expressed naturally.
    """

    image: ImageSpec
    network_name: str
    services: Sequence[ContainerSpec]
    label_namespace: str

    @property
    def managed_label(self) -> str:
        """Return the label used to mark runtime-owned resources."""
        return f"{self.label_namespace}.managed"

    @property
    def spec_fingerprint_label(self) -> str:
        """Return the label used to track container configuration."""
        return f"{self.label_namespace}.spec-fingerprint"

    def ensure(self, client: docker.DockerClient | None = None, *, rebuild_image: bool = False) -> dict[str, Container]:
        """Ensure the image, network, and all services are ready."""
        client = client or get_docker_client()

        ensure_image(client, self.image, rebuild=rebuild_image)

        ensure_network(client, self.network_name, labels={self.managed_label: "true"})

        containers: dict[str, Container] = {}

        for spec in self.services:
            container = ensure_container(
                client,
                spec,
                network_name=self.network_name,
                managed_label=self.managed_label,
                spec_fingerprint_label=self.spec_fingerprint_label,
            )

            wait_for_ready(container, timeout_seconds=spec.startup_timeout_seconds)

            containers[spec.name] = container

        return containers

    def stop(self, client: docker.DockerClient | None = None) -> None:
        """Stop managed services in reverse dependency order."""
        client = client or get_docker_client()

        for spec in reversed(tuple(self.services)):
            container = get_container(client, spec.name)

            if container is None:
                continue

            self._verify_managed(container)
            stop_container(container)

    def remove(self, client: docker.DockerClient | None = None, *, remove_network: bool = False) -> None:
        """Remove managed containers and optionally their network."""
        client = client or get_docker_client()

        for spec in reversed(tuple(self.services)):
            container = get_container(client, spec.name)

            if container is None:
                continue

            self._verify_managed(container)
            remove_container(container)

        if remove_network:
            try:
                network = client.networks.get(self.network_name)
                network.remove()

            except docker.errors.NotFound:
                pass

            except docker.errors.APIError as exc:
                raise DockerRuntimeError(f"Failed to remove Docker network {self.network_name!r}.") from exc

    def restart(self, client: docker.DockerClient | None = None) -> dict[str, Container]:
        """Restart all services and wait until they are ready."""
        client = client or get_docker_client()

        self.stop(client)

        return self.ensure(client)

    def status(self, client: docker.DockerClient | None = None) -> dict[str, ServiceStatus]:
        """Return runtime and health status for every service."""
        client = client or get_docker_client()

        statuses: dict[str, ServiceStatus] = {}

        for spec in self.services:
            container = get_container(client, spec.name)

            if container is None:
                statuses[spec.name] = ServiceStatus(status="missing", health=None)
                continue

            container.reload()

            statuses[spec.name] = ServiceStatus(status=container.status, health=get_container_health(container))

        return statuses

    def _verify_managed(self, container: Container) -> None:
        """Ensure a container is owned by this runtime."""
        container.reload()

        labels = container.attrs.get("Config", {}).get("Labels", {}) or {}

        if labels.get(self.managed_label) != "true":
            raise DockerRuntimeError(f"Container {container.name!r} is not managed by this runtime.")
