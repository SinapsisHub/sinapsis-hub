"""Credential storage for the Sinapsis SDK."""

import json
import os
import stat
from pathlib import Path
from typing import Protocol

import keyring
from keyring.errors import PasswordDeleteError
from platformdirs import user_config_dir

_SERVICE_NAME = "sinapsis-sdk"
_CREDENTIAL_FILE = "credentials.json"
# _DEFAULT_PROFILE = "default"


class CredentialStore(Protocol):
    """Interface for storing and retrieving credentials."""

    def get(self, name: str) -> str | None:
        """Retrieve a credential.

        Args:
            name: Name of the credential.

        Returns:
            The credential value, or None if it does not exist.
        """
        ...

    def set(self, name: str, value: str) -> None:
        """Store a credential.

        Args:
            name: Name of the credential.
            value: Credential value to store.
        """
        ...

    def delete(self, name: str) -> None:
        """Delete a credential.

        Args:
            name: Name of the credential.
        """
        ...


class KeyringCredentialStore:
    """Credential store backed by the operating system's credential manager."""

    def get(self, name: str) -> str | None:
        """Retrieve a credential from the OS credential store.

        Args:
            name: Name of the credential.

        Returns:
            The credential value, or None if it does not exist.
        """
        return keyring.get_password(_SERVICE_NAME, name)

    def set(self, name: str, value: str) -> None:
        """Store a credential in the OS credential store.

        Args:
            name: Name of the credential.
            value: Credential value to store.
        """
        keyring.set_password(_SERVICE_NAME, name, value)

    def delete(self, name: str) -> None:
        """Delete a credential from the OS credential store.

        Args:
            name: Name of the credential.
        """
        try:
            keyring.delete_password(_SERVICE_NAME, name)
        except PasswordDeleteError:
            pass


class FileCredentialStore:
    """Credential store backed by a local JSON file."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = path or Path(user_config_dir("sinapsis")) / _CREDENTIAL_FILE

    def get(self, name: str) -> str | None:
        """Retrieve a credential from the local file.

        Args:
            name: Name of the credential.

        Returns:
            The credential value, or None if it does not exist.
        """
        credentials = self._load()
        return credentials.get(name)

    def set(self, name: str, value: str) -> None:
        """Store a credential in the local file.

        Args:
            name: Name of the credential.
            value: Credential value to store.
        """
        credentials = self._load()
        credentials[name] = value
        self._save(credentials)

    def delete(self, name: str) -> None:
        """Delete a credential from the local file.

        Args:
            name: Name of the credential.
        """
        credentials = self._load()

        if name not in credentials:
            return

        del credentials[name]
        self._save(credentials)

    def _load(self) -> dict[str, str]:
        if not self._path.exists():
            return {}

        try:
            data = json.loads(self._path.read_text())
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid credential file: {self._path}") from exc

        if not isinstance(data, dict) or not all(
            isinstance(key, str) and isinstance(value, str) for key, value in data.items()
        ):
            raise ValueError(f"Invalid credential file: {self._path}")

        return data

    def _save(self, credentials: dict[str, str]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)

        temporary_path = self._path.with_suffix(".tmp")
        temporary_path.write_text(json.dumps(credentials, indent=2))
        os.chmod(temporary_path, stat.S_IRUSR | stat.S_IWUSR)
        temporary_path.replace(self._path)


def create_credential_store(use_file: bool = False) -> CredentialStore:
    """Create the configured credential store.

    Args:
        use_file: Whether to explicitly use file-based credential storage.

    Returns:
        A credential store instance.
    """
    if use_file:
        return FileCredentialStore()

    return KeyringCredentialStore()
