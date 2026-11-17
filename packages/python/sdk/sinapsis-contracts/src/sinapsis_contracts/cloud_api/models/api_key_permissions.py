"""Canonical scoped API-key permissions shared by Cloud, Management and CLI."""
from enum import StrEnum


class ApiKeyPermission(StrEnum):
    """Specific capabilities; an issued scope never overrides resource ownership."""

    AGENTS_READ = 'agents:read'
    AGENTS_EXECUTE = 'agents:execute'
    AGENTS_RESULTS_READ = 'agents:results:read'
    AGENTS_MANAGE = 'agents:manage'
    JOBS_CREATE = 'jobs:create'
    JOBS_READ = 'jobs:read'
    JOBS_CANCEL = 'jobs:cancel'
    JOBS_DELETE = 'jobs:delete'
    JOBS_RESULTS_READ = 'jobs:results:read'
    JOBS_STREAM = 'jobs:stream'
    FILES_READ = 'files:read'
    FILES_WRITE = 'files:write'
    WEBHOOKS_READ = 'webhooks:read'
    WEBHOOKS_MANAGE = 'webhooks:manage'
    PACKAGES_READ = 'packages:read'
    PACKAGES_WRITE = 'packages:write'
