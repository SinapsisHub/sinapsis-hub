import re
from importlib.metadata import version
from urllib.parse import urlparse

from sinapsis_api.env_vars import SINAPSIS_API_HOST_PORT, SINAPSIS_PACKAGE_INDEX

PACKAGE_DISTRIBUTION = "sinapsis-api"
# TODO: delete next line
SINAPSIS_PACKAGE_INDEX = "http://host.docker.internal:8080/simple"
PYTHON_VERSION = "3.13"

DOCKERFILE_TEMPLATE = """
FROM python:{python_version}-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV PYTHONUNBUFFERED=1 \\
    PYTHONDONTWRITEBYTECODE=1 \\
    UV_NO_CACHE=1

RUN uv pip install \\
    --system \\
    --index {package_index} \\
    "{package_distribution}=={package_version}"

WORKDIR /app

EXPOSE {api_host_port}
""".strip()


def get_insecure_host(index_url: str) -> str | None:
    """Return the host for an HTTP index that requires uv opt-in."""
    parsed = urlparse(index_url)

    if parsed.scheme != "http":
        return None

    return parsed.netloc


def get_installed_package_version() -> str:
    """Return the installed version of the Sinapsis API package."""
    return version(PACKAGE_DISTRIBUTION)


def get_runtime_image_name(package_version: str) -> str:
    """Return the local Docker image name for a package version."""
    return f"{PACKAGE_DISTRIBUTION}:{_docker_tag(package_version)}"


def get_runtime_dockerfile(package_version: str) -> str:
    """Return the Dockerfile used to build the local runtime image."""
    insecure_host = get_insecure_host(SINAPSIS_PACKAGE_INDEX)

    allow_insecure = f"--allow-insecure-host {insecure_host} \\\n    " if insecure_host else ""
    return DOCKERFILE_TEMPLATE.format(
        python_version=PYTHON_VERSION,
        package_index=SINAPSIS_PACKAGE_INDEX,
        allow_insecure=allow_insecure,
        package_distribution=PACKAGE_DISTRIBUTION,
        package_version=package_version,
        api_host_port=int(SINAPSIS_API_HOST_PORT),
    )


def _docker_tag(value: str) -> str:
    """Convert a package version into a valid Docker tag."""
    tag = re.sub(r"[^A-Za-z0-9_.-]+", "-", value).strip(".-")

    return tag or "local"
