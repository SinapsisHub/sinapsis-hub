from dataclasses import dataclass

from sinapsis_contracts.common.paths import BaseApiPaths


@dataclass(frozen=True)
class FilePaths:
    base: str = f"{BaseApiPaths.base}/files"
    upload: str = "/upload/{path:path}"
    list: str = "/ls/{prefix:path}"
    delete: str = "/{path:path}"
    create: str = "/create/{path:path}"
    search: str = "/search"
    get: str = "/get/{path:path}"
    fetch: str = "/fetch/{agent_id}/{file_id}"


FILE_PATHS = FilePaths()
