import hashlib
import json
import time
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field

from docker.errors import APIError, DockerException, NotFound
from docker.models.containers import Container
from docker.models.networks import Network

import docker

SECOND_IN_NS = 1_000_000_000


class DockerRuntimeError(RuntimeError):
    """Raised when a Docker runtime operation fails."""


@dataclass(frozen=True, slots=True)
class HealthCheck:
    """Docker health-check configuration for a managed service."""

    command: Sequence[str]
    interval_seconds: int = 10
    timeout_seconds: int = 5
    retries: int = 5
    start_period_seconds: int = 5

    def as_docker_config(self) -> dict[str, object]:
        """Return this health check in Docker SDK format."""
        return {
            "test": ["CMD", *self.command],
            "interval": self.interval_seconds * SECOND_IN_NS,
            "timeout": self.timeout_seconds * SECOND_IN_NS,
            "retries": self.retries,
            "start_period": self.start_period_seconds * SECOND_IN_NS,
        }


@dataclass(frozen=True, slots=True)
class ContainerSpec:
    """Declarative configuration for a Docker-managed service."""

    name: str
    image: str
    command: Sequence[str]
    environment: Mapping[str, str] = field(default_factory=dict)
    ports: Mapping[str, int] = field(default_factory=dict)
    labels: Mapping[str, str] = field(default_factory=dict)
    healthcheck: HealthCheck | None = None
    restart_policy: str = "unless-stopped"
    startup_timeout_seconds: float = 60.0

    def fingerprint(self) -> str:
        """Return a stable fingerprint used to detect configuration changes."""
        payload = {
            "name": self.name,
            "image": self.image,
            "command": list(self.command),
            "environment": dict(sorted(self.environment.items())),
            "ports": dict(sorted(self.ports.items())),
            "labels": dict(sorted(self.labels.items())),
            "healthcheck": (asdict(self.healthcheck) if self.healthcheck is not None else None),
            "restart_policy": self.restart_policy,
            "startup_timeout_seconds": self.startup_timeout_seconds,
        }

        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")

        return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class ServiceStatus:
    """Current Docker state for a managed service."""

    status: str
    health: str | None


def get_docker_client() -> docker.DockerClient:
    """Create a Docker client and verify that the daemon is reachable."""
    try:
        client = docker.from_env()
        client.ping()
        return client
    except DockerException as exc:
        raise DockerRuntimeError(
            "Docker is unavailable. Ensure Docker Desktop or the Docker daemon is running."
        ) from exc


def ensure_network(client: docker.DockerClient, name: str, *, labels: Mapping[str, str] | None = None) -> Network:
    """Return an existing Docker network or create a bridge network."""
    try:
        return client.networks.get(name)
    except NotFound:
        try:
            return client.networks.create(name=name, driver="bridge", labels=dict(labels or {}))
        except APIError as exc:
            raise DockerRuntimeError(f"Failed to create Docker network {name!r}.") from exc


def get_container(client: docker.DockerClient, name: str) -> Container | None:
    """Return a container by name, or None when it does not exist."""
    try:
        return client.containers.get(name)
    except NotFound:
        return None


def get_container_health(container: Container) -> str | None:
    """Return the Docker health state for a container."""
    container.reload()

    return container.attrs.get("State", {}).get("Health", {}).get("Status")


def get_container_logs(container: Container, *, tail: int = 100) -> str:
    """Return recent combined stdout and stderr from a container."""
    try:
        output = container.logs(stdout=True, stderr=True, tail=tail)
    except DockerException:
        return "<unable to retrieve container logs>"

    return output.decode("utf-8", errors="replace")


def create_container(
    client: docker.DockerClient,
    spec: ContainerSpec,
    *,
    network_name: str,
    managed_labels: Mapping[str, str],
) -> Container:
    """Create and start a managed container."""
    labels = {**dict(spec.labels), **dict(managed_labels)}

    kwargs: dict[str, object] = {
        "image": spec.image,
        "command": list(spec.command),
        "name": spec.name,
        "network": network_name,
        "environment": dict(spec.environment),
        "restart_policy": {"Name": spec.restart_policy},
        "labels": labels,
    }

    if spec.ports:
        kwargs["ports"] = dict(spec.ports)

    if spec.healthcheck is not None:
        kwargs["healthcheck"] = spec.healthcheck.as_docker_config()

    try:
        container = client.containers.create(**kwargs)
        container.start()
        return container

    except APIError as exc:
        container = get_container(client, spec.name)

        if container is not None:
            try:
                container.remove(force=True)
            except DockerException:
                pass

        raise DockerRuntimeError(f"Failed to create container {spec.name!r}.") from exc


def ensure_container(
    client: docker.DockerClient,
    spec: ContainerSpec,
    *,
    network_name: str,
    managed_label: str,
    spec_fingerprint_label: str,
) -> Container:
    """Ensure a managed container exists with the expected configuration.

    Containers are recreated automatically when their configuration or
    underlying image changes.
    """
    expected_image = client.images.get(spec.image)
    expected_fingerprint = spec.fingerprint()

    managed_labels = {managed_label: "true", spec_fingerprint_label: expected_fingerprint}

    container = get_container(client, spec.name)

    if container is None:
        return create_container(client, spec, network_name=network_name, managed_labels=managed_labels)

    container.reload()

    labels: Mapping[str, str] = container.attrs.get("Config", {}).get("Labels", {}) or {}

    if labels.get(managed_label) != "true":
        raise DockerRuntimeError(f"Container {spec.name!r} already exists but is not managed by this runtime.")

    config_changed = labels.get(spec_fingerprint_label) != expected_fingerprint

    image_changed = container.attrs.get("Image") != expected_image.id

    if config_changed or image_changed:
        remove_container(container)

        return create_container(client, spec, network_name=network_name, managed_labels=managed_labels)

    if container.status != "running":
        try:
            container.start()
        except APIError as exc:
            raise DockerRuntimeError(f"Failed to start container {spec.name!r}.") from exc

    elif get_container_health(container) == "unhealthy":
        try:
            container.restart(timeout=10)
        except APIError as exc:
            raise DockerRuntimeError(f"Failed to restart unhealthy container {spec.name!r}.") from exc

    return container


def wait_for_ready(container: Container, *, timeout_seconds: float = 60.0, poll_interval_seconds: float = 0.5) -> None:
    """Wait for a container to be running and, when configured, healthy."""
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        container.reload()

        state = container.attrs.get("State", {})
        status = state.get("Status")
        health = state.get("Health", {}).get("Status")

        if status in {"dead", "exited"}:
            raise DockerRuntimeError(
                f"Container {container.name!r} exited during startup.\n\n{get_container_logs(container)}"
            )

        if status == "running" and health is None:
            return

        if health == "healthy":
            return

        if health == "unhealthy":
            raise DockerRuntimeError(
                f"Container {container.name!r} became unhealthy.\n\n{get_container_logs(container)}"
            )

        time.sleep(poll_interval_seconds)

    raise DockerRuntimeError(
        f"Container {container.name!r} did not become ready within "
        f"{timeout_seconds:.0f} seconds.\n\n"
        f"{get_container_logs(container)}"
    )


def stop_container(container: Container, *, timeout_seconds: int = 10) -> None:
    """Stop a container if it is currently running."""
    container.reload()

    if container.status != "running":
        return

    try:
        container.stop(timeout=timeout_seconds)
    except APIError as exc:
        raise DockerRuntimeError(f"Failed to stop container {container.name!r}.") from exc


def remove_container(container: Container) -> None:
    """Stop and remove a container."""
    try:
        container.reload()

        if container.status == "running":
            container.stop(timeout=10)

        container.remove(force=True)

    except NotFound:
        return

    except APIError as exc:
        raise DockerRuntimeError(f"Failed to remove container {container.name!r}.") from exc
