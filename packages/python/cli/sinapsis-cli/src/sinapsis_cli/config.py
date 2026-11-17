"""CLI configuration and execution profiles."""

import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from sinapsis_sdk.cloud_api._config import ConfigStore

DEFAULT_CLOUD_URL = "https://api.sinapsis.tech"
DEFAULT_LOCAL_URL = "http://localhost:8000"
DEFAULT_VENV = ".venv"
DEFAULT_PROFILE = "local"

PROFILE_ENV_VAR = "SINAPSIS_PROFILE"
LEGACY_EXECUTION_ENV_VARS = ("SINAPSIS_EXECUTION_MODE", "SINAPSIS_EXECUTE_MODE")

_PROFILE_NAME_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ExecutionBackend(str, Enum):
    """Execution backends supported by the CLI."""

    LOCAL_VENV = "local-venv"
    LOCAL_API = "local-api"
    CLOUD = "cloud"


_BACKEND_ALIASES = {
    "local": ExecutionBackend.LOCAL_VENV,
    "local-venv": ExecutionBackend.LOCAL_VENV,
    "local_api": ExecutionBackend.LOCAL_API,
    "local-api": ExecutionBackend.LOCAL_API,
    "cloud": ExecutionBackend.CLOUD,
}

_DEFAULT_PROFILE_FOR_BACKEND = {
    ExecutionBackend.LOCAL_VENV: "local",
    ExecutionBackend.LOCAL_API: "local-api",
    ExecutionBackend.CLOUD: "cloud",
}


@dataclass(frozen=True)
class Profile:
    """Configuration for a Sinapsis execution profile.

    A profile is a named execution environment. ``backend`` determines the
    base command composition, while ``command_sets`` can add optional command
    providers without changing other profiles.
    """

    name: str
    backend: ExecutionBackend
    api_url: str | None = None
    venv: str | None = None
    authenticated: bool = False
    command_sets: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized_name = validate_profile_name(self.name)
        object.__setattr__(self, "name", normalized_name)

        if not isinstance(self.backend, ExecutionBackend):
            object.__setattr__(self, "backend", validate_backend(self.backend))

        if self.api_url is not None:
            normalized_url = self.api_url.strip().rstrip("/")
            object.__setattr__(self, "api_url", normalized_url or None)

        if self.venv is not None and not self.venv.strip():
            object.__setattr__(self, "venv", None)

        normalized_command_sets = tuple(
            dict.fromkeys(command_set.strip() for command_set in self.command_sets if command_set.strip())
        )
        object.__setattr__(self, "command_sets", normalized_command_sets)


@dataclass
class CLIConfig:
    """Sinapsis CLI configuration."""

    default_profile: str = DEFAULT_PROFILE
    profiles: dict[str, Profile] | None = None

    def __post_init__(self) -> None:
        if self.profiles is None:
            self.profiles = _default_profiles()

        if self.default_profile not in self.profiles:
            self.default_profile = DEFAULT_PROFILE

        if self.default_profile not in self.profiles:
            self.default_profile = next(iter(self.profiles))

    @property
    def profile(self) -> Profile:
        """Return the configured default profile."""
        return self.get_profile(self.default_profile)

    @property
    def execute_mode(self) -> str:
        """Return the legacy execution-mode value for compatibility."""
        return legacy_mode_for_backend(self.profile.backend)

    @execute_mode.setter
    def execute_mode(self, mode: str) -> None:
        """Set the default profile using a legacy execution-mode value."""
        backend = validate_backend(mode)
        self.default_profile = find_profile_for_backend(self, backend).name

    def get_profile(self, name: str) -> Profile:
        """Return a profile by name.

        Args:
            name: Profile name.

        Raises:
            ValueError: If the requested profile does not exist.
        """
        assert self.profiles is not None

        try:
            return self.profiles[name]
        except KeyError as exception:
            available = ", ".join(sorted(self.profiles))
            raise ValueError(f"Unknown profile {name!r}. Available profiles: {available}") from exception


def validate_profile_name(name: str) -> str:
    """Validate and normalize a profile name."""
    normalized = name.strip()

    if not normalized or not _PROFILE_NAME_PATTERN.fullmatch(normalized):
        raise ValueError(
            "Profile names must start with a letter or number and contain only letters, numbers, '.', '_', or '-'."
        )

    return normalized


def validate_backend(value: str | ExecutionBackend) -> ExecutionBackend:
    """Validate and normalize an execution backend."""
    if isinstance(value, ExecutionBackend):
        return value

    normalized = value.strip().lower()

    try:
        return _BACKEND_ALIASES[normalized]
    except KeyError as exception:
        available = ", ".join(backend.value for backend in ExecutionBackend)
        raise ValueError(f"Unknown execution backend {value!r}. Available backends: {available}") from exception


def validate_execute_mode(mode: str) -> str:
    """Validate a legacy execution mode and return its canonical value."""
    return legacy_mode_for_backend(validate_backend(mode))


def legacy_mode_for_backend(backend: ExecutionBackend) -> str:
    """Return the legacy execution-mode name for a backend."""
    if backend is ExecutionBackend.LOCAL_VENV:
        return "local"
    return backend.value


def _default_profiles() -> dict[str, Profile]:
    """Return the built-in execution profiles."""
    return {
        "local": Profile(
            name="local",
            backend=ExecutionBackend.LOCAL_VENV,
            venv=DEFAULT_VENV,
            authenticated=False,
        ),
        "cloud": Profile(
            name="cloud",
            backend=ExecutionBackend.CLOUD,
            api_url=DEFAULT_CLOUD_URL,
            authenticated=True,
        ),
        "local-api": Profile(
            name="local-api",
            backend=ExecutionBackend.LOCAL_API,
            api_url=DEFAULT_LOCAL_URL,
            authenticated=False,
        ),
    }


def load_config() -> CLIConfig:
    """Load CLI configuration from the shared SDK configuration file.

    The loader accepts both the profile-aware schema and the previous
    ``execute_mode``/``base_url`` schema. Saving the configuration writes the
    new schema while preserving unrelated SDK settings.
    """
    store = ConfigStore()
    data = store.load_raw()
    if not isinstance(data, dict):
        data = {}

    profiles = _load_profiles(data.get("profiles"))
    defaults = _default_profiles()
    defaults.update(profiles)

    default_profile = data.get("default_profile")

    if not isinstance(default_profile, str) or default_profile not in defaults:
        default_profile = _legacy_default_profile(data, defaults)

    return CLIConfig(default_profile=default_profile, profiles=defaults)


def save_config(config: CLIConfig) -> None:
    """Persist CLI configuration while preserving SDK configuration."""
    store = ConfigStore()
    data = store.load_raw()
    if not isinstance(data, dict):
        data = {}

    assert config.profiles is not None

    if config.default_profile not in config.profiles:
        raise ValueError(f"Default profile {config.default_profile!r} does not exist.")

    data["default_profile"] = config.default_profile

    # Remove fields from the previous CLI profile model when rewriting.
    data.pop("active_profile", None)
    data.pop("execute_mode", None)

    profiles: dict[str, dict[str, Any]] = {}

    for name, profile in config.profiles.items():
        profile_data: dict[str, Any] = {
            "backend": profile.backend.value,
            "authenticated": profile.authenticated,
        }

        if profile.api_url is not None:
            profile_data["api_url"] = profile.api_url.rstrip("/")

        if profile.venv is not None:
            profile_data["venv"] = profile.venv

        if profile.command_sets:
            profile_data["command_sets"] = list(profile.command_sets)

        profiles[name] = profile_data

    data["profiles"] = profiles
    store.save_raw(data)


def get_execution_profile(profile_name: str | None = None, *, config: CLIConfig | None = None) -> Profile:
    """Resolve the effective execution profile.

    Resolution order is: explicit profile, ``SINAPSIS_PROFILE``, legacy
    execution-mode environment variables, then the configured default profile.
    """
    config = config or load_config()

    if profile_name is not None:
        return config.get_profile(profile_name)

    environment_profile = os.getenv(PROFILE_ENV_VAR)
    if environment_profile and environment_profile.strip():
        return config.get_profile(environment_profile.strip())

    for variable in LEGACY_EXECUTION_ENV_VARS:
        value = os.getenv(variable)
        if not value or not value.strip():
            continue

        candidate = value.strip()
        if config.profiles and candidate in config.profiles:
            return config.get_profile(candidate)

        return find_profile_for_backend(config, validate_backend(candidate))

    return config.profile


def get_execution_mode() -> str:
    """Return the effective legacy execution-mode value."""
    return legacy_mode_for_backend(get_execution_profile().backend)


def find_profile_for_backend(config: CLIConfig, backend: ExecutionBackend) -> Profile:
    """Find the preferred profile for a backend."""
    assert config.profiles is not None

    canonical_name = _DEFAULT_PROFILE_FOR_BACKEND[backend]
    canonical = config.profiles.get(canonical_name)
    if canonical is not None and canonical.backend is backend:
        return canonical

    matches = [profile for profile in config.profiles.values() if profile.backend is backend]

    if len(matches) == 1:
        return matches[0]

    if not matches:
        raise ValueError(f"No configured profile uses backend {backend.value!r}.")

    names = ", ".join(sorted(profile.name for profile in matches))
    raise ValueError(
        f"Multiple profiles use backend {backend.value!r}: {names}. "
        f"Select one with {PROFILE_ENV_VAR} or an explicit profile name."
    )


def set_default_profile(name: str) -> CLIConfig:
    """Set and persist the default profile."""
    config = load_config()
    config.get_profile(name)
    config.default_profile = name
    save_config(config)
    return config


def set_execute_mode(mode: str) -> CLIConfig:
    """Set the default profile from a legacy execution-mode value."""
    config = load_config()
    profile = find_profile_for_backend(config, validate_backend(mode))
    config.default_profile = profile.name
    save_config(config)
    return config


def set_profile(profile: Profile) -> CLIConfig:
    """Create or replace an execution profile."""
    validate_profile_name(profile.name)
    config = load_config()
    assert config.profiles is not None
    config.profiles[profile.name] = profile
    save_config(config)
    return config


def delete_profile(name: str) -> CLIConfig:
    """Delete an execution profile.

    Raises:
        ValueError: If the profile does not exist or is the default profile.
    """
    config = load_config()
    assert config.profiles is not None

    if name == config.default_profile:
        raise ValueError(f"Cannot delete the default profile {name!r}. Choose another default profile first.")

    if name not in config.profiles:
        raise ValueError(f"Unknown profile {name!r}.")

    del config.profiles[name]
    save_config(config)
    return config


def _legacy_default_profile(data: dict[str, Any], profiles: dict[str, Profile]) -> str:
    """Resolve the default profile from the previous configuration schema."""
    legacy = data.get("active_profile") or data.get("execute_mode")

    if isinstance(legacy, str):
        if legacy in profiles:
            return legacy

        try:
            backend = validate_backend(legacy)
        except ValueError:
            backend = ExecutionBackend.LOCAL_VENV

        canonical_name = _DEFAULT_PROFILE_FOR_BACKEND[backend]
        if canonical_name in profiles:
            return canonical_name

    if DEFAULT_PROFILE in profiles:
        return DEFAULT_PROFILE

    return next(iter(profiles))


def _load_profiles(raw_profiles: object) -> dict[str, Profile]:
    """Load profiles from raw configuration data."""
    profiles: dict[str, Profile] = {}

    if not isinstance(raw_profiles, dict):
        return profiles

    for name, values in raw_profiles.items():
        if not isinstance(name, str) or not isinstance(values, dict):
            continue

        try:
            validate_profile_name(name)
        except ValueError:
            continue

        raw_backend = values.get("backend") or values.get("execution_mode")

        if raw_backend is None:
            raw_backend = name if name in _BACKEND_ALIASES else None

        if not isinstance(raw_backend, str):
            continue

        try:
            backend = validate_backend(raw_backend)
        except ValueError:
            continue

        api_url = values.get("api_url", values.get("base_url"))
        if not isinstance(api_url, str) or not api_url.strip():
            api_url = None
        else:
            api_url = api_url.rstrip("/")

        venv = values.get("venv")
        if not isinstance(venv, str) or not venv.strip():
            venv = None

        authenticated = values.get("authenticated", backend is ExecutionBackend.CLOUD)

        raw_command_sets = values.get("command_sets", ())
        command_sets: tuple[str, ...]

        if isinstance(raw_command_sets, (list, tuple)):
            command_sets = tuple(item for item in raw_command_sets if isinstance(item, str) and item.strip())
        else:
            command_sets = ()

        profiles[name] = Profile(
            name=name,
            backend=backend,
            api_url=api_url,
            venv=venv,
            authenticated=bool(authenticated),
            command_sets=command_sets,
        )

    return profiles
