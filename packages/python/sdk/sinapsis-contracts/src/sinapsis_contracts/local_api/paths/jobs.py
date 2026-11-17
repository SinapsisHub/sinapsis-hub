from dataclasses import dataclass

from sinapsis_contracts.common.paths import BaseApiPaths


@dataclass(frozen=True)
class _JobPaths:
    base: str = f"{BaseApiPaths.base}/jobs"
    start: str = ""
    job: str = "/{job_id}"
    cancel: str = "/{job_id}/cancel"
    feedback: str = "/{job_id}/feedback"
    events: str = "/{job_id}//events"


API_JOB_PATHS = _JobPaths()
