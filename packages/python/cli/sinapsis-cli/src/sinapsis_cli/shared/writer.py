"""Persist decoded Sinapsis job results to disk."""

from __future__ import annotations

import base64
import dataclasses
import json
import re
from pathlib import Path
from typing import Any

try:
    from pydantic import BaseModel
except ImportError:  # pragma: no cover
    BaseModel = None  # type: ignore[assignment,misc]


_SAFE_NAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


class ResultWriter:
    """Write decoded job results and their artifacts to disk.

    Results are grouped by agent and template:

        results/
            <agent_id>/
                <template_name>/
                    result_001.json
                    result_001_image_001.png
                    result_001_file_001.pdf
                    ...

    A separate counter is maintained for every agent/template pair.
    """

    def __init__(self, save_dir: str | Path = "results") -> None:
        self.save_dir = Path(save_dir)

    def write(self, result: Any) -> list[Path]:
        """Write all data entries contained in a job result.

        Returns:
            Paths written to disk.
        """
        written: list[Path] = []

        agent_id = _safe_name(result.agent_id, "unknown-agent")

        for idx, entry in enumerate(result.template_data or []):
            if not entry.output:
                continue

            result_dir = self.save_dir / agent_id / entry.template_name
            result_dir.mkdir(parents=True, exist_ok=True)

            result_number = self._next_result_number(result_dir)
            prefix = f"result_{result_number:03d}"

            # exclude the actual data containers
            metadata = result.model_dump(exclude={"template_data": {idx: {"output": True}}})

            artifacts = self._write_container(entry.output, result_dir=result_dir, prefix=prefix)

            metadata["artifacts"] = [path.name for path in artifacts if path.name != f"{prefix}.json"]

            metadata_path = result_dir / f"{prefix}.json"
            metadata_path.write_text(
                json.dumps(metadata, indent=2, ensure_ascii=False, default=_json_value) + "\n",
                encoding="utf-8",
            )

            written.append(metadata_path)
            written.extend(artifacts)

        return written

    def write_container(self, container: Any, *, agent_id: str | None, stream_name: str | None = None) -> list[Path]:
        """Persist a native DataContainer without a cloud result wrapper.

        Args:
            container: DataContainer-like object to persist.
            agent_id: Logical agent identifier used for the output directory.
            stream_name: Optional job or stream identifier used as the second
                directory component.

        Returns:
            Paths written to disk.
        """
        result_dir = self.save_dir / _safe_name(agent_id, "unknown-agent") / _safe_name(stream_name, "events")
        result_dir.mkdir(parents=True, exist_ok=True)

        result_number = self._next_result_number(result_dir)
        prefix = f"result_{result_number:03d}"

        artifacts = self._write_container(container, result_dir=result_dir, prefix=prefix)

        metadata = {
            "container_id": getattr(container, "container_id", None),
            "artifacts": [path.name for path in artifacts],
        }

        metadata_path = result_dir / f"{prefix}.json"
        metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False, default=_json_value) + "\n",
            encoding="utf-8",
        )

        return [metadata_path, *artifacts]

    def _write_container(self, container: Any, *, result_dir: Path, prefix: str) -> list[Path]:
        """Write the contents of a DataContainer."""
        written: list[Path] = []

        packet_groups = (
            "images",
            "audios",
            "texts",
            "llm_conversations",
            "files",
            "time_series",
            "data_frames",
            "binary_data",
        )

        for group_name in packet_groups:
            packets = getattr(container, group_name)

            if not packets:
                continue

            for index, packet in enumerate(packets, start=1):
                paths = self._write_packet(
                    packet, group_name=group_name, index=index, result_dir=result_dir, prefix=prefix
                )
                written.extend(paths)

        generic_data = getattr(container, "generic_data", None)

        if generic_data:
            path = result_dir / f"{prefix}_generic.json"
            path.write_text(
                json.dumps(generic_data, indent=2, ensure_ascii=False, default=_json_value) + "\n",
                encoding="utf-8",
            )
            written.append(path)

        return written

    def _write_packet(self, packet: Any, *, group_name: str, index: int, result_dir: Path, prefix: str) -> list[Path]:
        """Persist one packet."""
        payload = _find_payload(packet)

        if payload is not None:
            path = self._write_payload(
                payload,
                packet=packet,
                group_name=group_name,
                index=index,
                result_dir=result_dir,
                prefix=prefix,
            )

            if path is not None:
                return [path]

        # No directly persistable payload was found. Preserve the packet
        # itself as JSON so no information is silently discarded.
        path = result_dir / f"{prefix}_{group_name}_{index:03d}.json"

        path.write_text(
            json.dumps(_json_value(packet), indent=2, ensure_ascii=False, default=_json_value) + "\n",
            encoding="utf-8",
        )

        return [path]

    def _write_payload(
        self,
        payload: Any,
        *,
        packet: Any,
        group_name: str,
        index: int,
        result_dir: Path,
        prefix: str,
    ) -> Path | None:
        """Write a packet payload using the most appropriate representation."""
        suffix = _extension_for(packet, payload, group_name)

        path = result_dir / (f"{prefix}_{_safe_name(group_name, 'data')}_{index:03d}{suffix}")

        if isinstance(payload, bytes):
            path.write_bytes(payload)
            return path

        if isinstance(payload, bytearray):
            path.write_bytes(bytes(payload))
            return path

        if isinstance(payload, memoryview):
            path.write_bytes(payload.tobytes())
            return path

        if isinstance(payload, Path):
            if payload.is_file():
                path.write_bytes(payload.read_bytes())
                return path

            return None

        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
            return path

        if hasattr(payload, "save"):
            try:
                payload.save(path)
                return path
            except (OSError, TypeError, ValueError):
                pass

        if hasattr(payload, "tofile"):
            try:
                payload.tofile(path)
                return path
            except (OSError, TypeError, ValueError):
                pass

        return None

    @staticmethod
    def _next_result_number(result_dir: Path) -> int:
        """Return the next result number for an agent/template directory."""
        numbers: list[int] = []

        for path in result_dir.glob("result_*.json"):
            match = re.match(r"result_(\d+)\.json$", path.name)

            if match:
                numbers.append(int(match.group(1)))

        return max(numbers, default=0) + 1


def _find_payload(packet: Any) -> Any:
    """Find the most likely binary/text payload in a packet.

    Packet implementations can differ, so inspect their dataclass/model
    fields rather than requiring the CLI to know every packet schema.
    """
    preferred_names = (
        "data",
        "payload",
        "content",
        "value",
        "bytes",
        "file",
        "path",
        "image",
        "audio",
        "text",
    )

    values = _object_values(packet)

    for name in preferred_names:
        if name not in values:
            continue

        value = values[name]

        if _is_payload(value):
            return value

    # Fall back to any directly writable value.
    for value in values.values():
        if _is_payload(value):
            return value

    return None


def _object_values(value: Any) -> dict[str, Any]:
    """Return fields from common Python model types."""
    if value is None:
        return {}

    if BaseModel is not None and isinstance(value, BaseModel):
        return dict(value.model_dump())

    if dataclasses.is_dataclass(value):
        return {field.name: getattr(value, field.name) for field in dataclasses.fields(value)}

    if hasattr(value, "__dict__"):
        return {key: item for key, item in vars(value).items() if not key.startswith("_")}

    return {}


def _is_payload(value: Any) -> bool:
    """Return whether a value can be directly persisted."""
    return (
        isinstance(value, (bytes, bytearray, memoryview, str, Path))
        or hasattr(value, "save")
        or hasattr(value, "tofile")
    )


def _extension_for(packet: Any, payload: Any, group_name: str) -> str:
    """Determine a useful extension for a payload."""
    if isinstance(payload, Path):
        suffix = payload.suffix.lower()
        if suffix:
            return suffix

    values = _object_values(packet)

    for key in ("extension", "file_extension", "mime_type", "media_type"):
        value = values.get(key)

        if not isinstance(value, str):
            continue

        extension = _extension_from_value(value)

        if extension:
            return extension

    defaults = {
        "images": ".bin",
        "audios": ".bin",
        "texts": ".txt",
        "llm_conversations": ".json",
        "files": ".bin",
        "time_series": ".json",
        "data_frames": ".json",
        "binary_data": ".bin",
    }

    return defaults.get(group_name, ".json")


def _extension_from_value(value: str) -> str | None:
    """Convert a MIME type or extension into a file extension."""
    value = value.lower().strip()

    if value.startswith("."):
        return value

    mime_extensions = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/jpg": ".jpg",
        "image/webp": ".webp",
        "image/gif": ".gif",
        "audio/wav": ".wav",
        "audio/x-wav": ".wav",
        "audio/mpeg": ".mp3",
        "audio/ogg": ".ogg",
        "application/pdf": ".pdf",
        "application/json": ".json",
        "text/plain": ".txt",
        "text/csv": ".csv",
        "application/zip": ".zip",
    }

    return mime_extensions.get(value)


def _json_value(value: Any) -> Any:
    """Convert common Python objects into JSON-compatible values."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value

    if isinstance(value, Path):
        return str(value)

    if isinstance(value, bytes):
        return {"encoding": "base64", "data": base64.b64encode(value).decode("ascii")}

    if isinstance(value, bytearray):
        return {"encoding": "base64", "data": base64.b64encode(bytes(value)).decode("ascii")}

    if isinstance(value, memoryview):
        return {"encoding": "base64", "data": base64.b64encode(value.tobytes()).decode("ascii")}

    if BaseModel is not None and isinstance(value, BaseModel):
        return value.model_dump(mode="json")

    if dataclasses.is_dataclass(value):
        return dataclasses.asdict(value)

    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [_json_value(item) for item in value]

    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except (AttributeError, TypeError, ValueError):
            pass

    values = _object_values(value)

    if values:
        return {str(key): _json_value(item) for key, item in values.items()}

    return str(value)


def _safe_name(value: Any, fallback: str) -> str:
    """Make an agent/template name safe for use as a directory name."""
    if value is None:
        return fallback

    value = str(value).strip()

    if not value:
        return fallback

    value = _SAFE_NAME_RE.sub("_", value)
    value = value.strip("._")

    return value or fallback
