"""Persistent configuration for the Sinapsis SDK."""

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

import tomli_w

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

from platformdirs import user_config_dir

from sinapsis_sdk.cloud_api.cloud_config import CloudAPIConfig

_CONFIG_DIR_NAME = "sinapsis"
_CONFIG_FILE_NAME = "config.toml"


class ConfigStore:
    """Persistent store for non-sensitive SDK configuration."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path(user_config_dir(_CONFIG_DIR_NAME)) / _CONFIG_FILE_NAME

    @property
    def path(self) -> Path:
        """Return the path of the configuration file."""
        return self._path

    def load(self) -> CloudAPIConfig:
        """Load SDK configuration from disk."""
        if not self._path.exists():
            return CloudAPIConfig()

        data = self._load_raw()

        # Ignore CLI-specific configuration and any other keys that
        # do not belong to APIConfig.
        api_fields = {"api_url", "timeout"}

        sdk_data = {key: value for key, value in data.items() if key in api_fields}

        try:
            return CloudAPIConfig(**sdk_data)
        except TypeError as exc:
            raise ValueError(f"Invalid configuration file: {self._path}") from exc

    def save(self, config: CloudAPIConfig) -> None:
        """Save SDK configuration without destroying CLI configuration."""
        self._path.parent.mkdir(parents=True, exist_ok=True)

        # Preserve existing configuration, including CLI-specific
        # settings such as execute_mode and profiles.
        data = self._load_raw() if self._path.exists() else {}

        # Replace only SDK-owned values.
        data.update(asdict(config))
        data["timeout"] = config.timeout

        self._write_raw(data)

    def load_raw(self) -> dict[str, Any]:
        """Load the complete configuration file.

        This is primarily useful to applications such as the CLI that
        share the configuration file but own additional settings.
        """
        return self._load_raw()

    def save_raw(self, data: dict[str, Any]) -> None:
        """Save the complete configuration file."""
        self._path.parent.mkdir(parents=True, exist_ok=True)

        self._write_raw(data)

    def _load_raw(self) -> dict[str, Any]:
        """Load the complete TOML configuration."""
        if not self._path.exists():
            return {}

        try:
            with self._path.open("rb") as file:
                data = tomllib.load(file)
        except tomllib.TOMLDecodeError as exc:
            raise ValueError(f"Invalid configuration file: {self._path}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"Invalid configuration file: {self._path}")

        return dict(data)

    def _write_raw(self, data: dict[str, Any]) -> None:
        """Write the complete TOML configuration."""
        with self._path.open("wb") as file:
            tomli_w.dump(data, file)
