import io
import tarfile
from dataclasses import dataclass

from docker.errors import APIError, BuildError, ImageNotFound
from docker.models.images import Image

import docker

from .base import DockerRuntimeError


@dataclass(frozen=True, slots=True)
class ImageSpec:
    """Declarative configuration for a locally built Docker image."""

    name: str
    dockerfile: str


def ensure_image(client: docker.DockerClient, spec: ImageSpec, *, rebuild: bool = False) -> Image:
    """Return the requested image, building it locally when necessary."""
    if not rebuild:
        try:
            return client.images.get(spec.name)
        except ImageNotFound:
            pass

    return build_image(client, spec)


def build_image(client: docker.DockerClient, spec: ImageSpec) -> Image:
    """Build an image from an in-memory Dockerfile."""
    context = _build_context(spec.dockerfile)

    try:
        image, _ = client.images.build(
            fileobj=context,
            custom_context=True,
            dockerfile="Dockerfile",
            tag=spec.name,
            rm=True,
            forcerm=True,
            pull=True,
            extra_hosts={"host.docker.internal": "host-gateway"},
        )

        return image

    except BuildError as exc:
        raise DockerRuntimeError(f"Failed to build Docker image {spec.name!r}.\n\n{_format_build_error(exc)}") from exc

    except APIError as exc:
        raise DockerRuntimeError(f"Docker failed while building image {spec.name!r}.") from exc


def _build_context(dockerfile: str) -> io.BytesIO:
    """Create an in-memory tar build context containing a Dockerfile."""
    buffer = io.BytesIO()
    dockerfile_bytes = dockerfile.encode("utf-8")

    with tarfile.open(fileobj=buffer, mode="w") as archive:
        info = tarfile.TarInfo(name="Dockerfile")
        info.size = len(dockerfile_bytes)

        archive.addfile(info, io.BytesIO(dockerfile_bytes))

    buffer.seek(0)

    return buffer


def _format_build_error(exc: BuildError) -> str:
    """Convert Docker build output into readable error text."""
    messages: list[str] = []

    for entry in exc.build_log:
        message = entry.get("error") or entry.get("stream")

        if message:
            messages.append(message.strip())

    return "\n".join(messages)
