from urllib.parse import urlparse

from sinapsis_api.env_vars import (
    SINAPSIS_API_HOST_PORT,
    SINAPSIS_API_ROUTER_AGENT_ENDPOINT,
    SINAPSIS_API_ROUTER_API_ENDPOINT,
    SINAPSIS_API_ROUTER_STREAM_ENDPOINT,
)

from ._file import get_installed_package_version, get_runtime_dockerfile, get_runtime_image_name
from .base import ContainerSpec, HealthCheck
from .image import ImageSpec
from .runtime import DockerRuntime

NETWORK_NAME = "sinapsis"

API_CONTAINER_NAME = "sinapsis-api"
ROUTER_CONTAINER_NAME = "sinapsis-agent-router"

LABEL_NAMESPACE = "ai.sinapsis.runtime"


def get_runtime() -> DockerRuntime:
    """Return the Docker runtime for the Sinapsis API stack."""
    package_version = get_installed_package_version()
    image_name = get_runtime_image_name(package_version)

    return DockerRuntime(
        image=ImageSpec(name=image_name, dockerfile=get_runtime_dockerfile(package_version)),
        network_name=NETWORK_NAME,
        services=(_router_spec(image_name), _api_spec(image_name)),
        label_namespace=LABEL_NAMESPACE,
    )


def _router_spec(image_name: str) -> ContainerSpec:
    """Return the container specification for the agent router."""
    return ContainerSpec(
        name=ROUTER_CONTAINER_NAME,
        image=image_name,
        command=("python", "-m", "sinapsis_api.agent_router"),
        environment={
            "SINAPSIS_API_ROUTER_API_ENDPOINT": _bind_endpoint(SINAPSIS_API_ROUTER_API_ENDPOINT),
            "SINAPSIS_API_ROUTER_AGENT_ENDPOINT": _bind_endpoint(SINAPSIS_API_ROUTER_AGENT_ENDPOINT),
            "SINAPSIS_API_ROUTER_STREAM_ENDPOINT": _bind_endpoint(SINAPSIS_API_ROUTER_STREAM_ENDPOINT),
        },
        healthcheck=HealthCheck(
            command=("python", "-m", "sinapsis_api.api.healthcheck"),
            interval_seconds=5,
            timeout_seconds=5,
            retries=10,
            start_period_seconds=5,
        ),
        startup_timeout_seconds=60,
    )


def _api_spec(image_name: str) -> ContainerSpec:
    """Return the container specification for the HTTP API."""
    api_port = int(SINAPSIS_API_HOST_PORT)

    return ContainerSpec(
        name=API_CONTAINER_NAME,
        image=image_name,
        command=(
            "gunicorn",
            "sinapsis_api.api.main:app",
            "--workers",
            "5",
            "--worker-class",
            "uvicorn.workers.UvicornWorker",
            "--bind",
            f"0.0.0.0:{api_port}",
            "--access-logfile",
            "-",
            "--error-logfile",
            "-",
            "--log-level",
            "info",
        ),
        environment={
            "SINAPSIS_API_ROUTER_API_ENDPOINT": _service_endpoint(SINAPSIS_API_ROUTER_API_ENDPOINT),
            "SINAPSIS_API_ROUTER_AGENT_ENDPOINT": _service_endpoint(SINAPSIS_API_ROUTER_AGENT_ENDPOINT),
            "SINAPSIS_API_ROUTER_STREAM_ENDPOINT": _service_endpoint(SINAPSIS_API_ROUTER_STREAM_ENDPOINT),
        },
        ports={f"{api_port}/tcp": api_port},
        healthcheck=HealthCheck(
            command=(
                "python",
                "-c",
                (
                    "import urllib.request; "
                    "urllib.request.urlopen("
                    f"'http://127.0.0.1:{api_port}/api/v1/health', "
                    "timeout=5)"
                ),
            ),
            interval_seconds=10,
            timeout_seconds=6,
            retries=5,
            start_period_seconds=10,
        ),
        startup_timeout_seconds=60,
    )


def _bind_endpoint(endpoint: str) -> str:
    """Return the router-side bind endpoint."""
    return f"tcp://0.0.0.0:{_endpoint_port(endpoint)}"


def _service_endpoint(endpoint: str) -> str:
    """Return the API-side endpoint for the router container."""
    return f"tcp://{ROUTER_CONTAINER_NAME}:{_endpoint_port(endpoint)}"


def _endpoint_port(endpoint: str) -> int:
    """Extract the port from a configured TCP endpoint."""
    parsed = urlparse(endpoint)

    if parsed.scheme != "tcp":
        raise ValueError(f"Expected a TCP router endpoint, got {endpoint!r}.")

    if parsed.port is None:
        raise ValueError(f"Router endpoint does not define a port: {endpoint!r}.")

    return parsed.port
