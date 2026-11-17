"""File operations for the Sinapsis API."""

from pathlib import Path

from sinapsis_contracts.cloud_api.paths import FILE_PATHS

from sinapsis_sdk.common.base_resource_client import BaseClientResource


class FilesResource(BaseClientResource):
    """Provides operations for user-managed files."""

    def __init__(self, http) -> None:
        super().__init__(http, FILE_PATHS.base)

    async def upload(self, file: Path, path: str | None = None) -> dict[str, object]:
        """Upload a file to the user's private storage.

        Args:
            file: Local file to upload.
            path: Destination path relative to the user's storage root.
                Defaults to the local filename.

        Returns:
            Upload metadata returned by the API.

        Raises:
            FileNotFoundError: If the local file does not exist.
            ValueError: If the file path is not a regular file.
        """
        if not file.exists():
            raise FileNotFoundError(f"File does not exist: {file}")

        if not file.is_file():
            raise ValueError(f"Path is not a file: {file}")

        destination = path or file.name

        with file.open("rb") as file_handle:
            return await self._http.post(
                self._path(FILE_PATHS.upload, path=destination), files={"file": (file.name, file_handle)}
            )

    async def list(self, prefix: str = "") -> dict[str, object]:
        """List files in private storage."""
        return await self._http.get(self._path(FILE_PATHS.list, prefix=prefix.lstrip("/")))

    async def create(self, path: str) -> dict[str, object]:
        """Create a file or directory in private storage."""
        return await self._http.post(self._path(FILE_PATHS.create, path=path))

    async def search(self, file_name: str, exact: bool = False) -> dict[str, object]:
        """Search private storage."""
        return await self._http.post(self._path(FILE_PATHS.search), params={"file_name": file_name, "exact": exact})

    async def view(self, path: str) -> bytes:
        """View a file from private storage."""
        return await self.get(path)

    async def get(self, path: str) -> bytes:
        """Fetch an agent file."""
        return await self._http.get(self._path(FILE_PATHS.get, path=path), raw=True)

    async def fetch(self, agent_id: str, file_id: str) -> bytes:
        """Fetch an agent file."""
        return await self._http.get(self._path(FILE_PATHS.fetch, agent_id=agent_id, file_id=file_id), raw=True)

    async def delete(self, path: str) -> None:
        """Delete a file from private storage."""
        await self._http.delete(self._path(FILE_PATHS.delete, path=path))
