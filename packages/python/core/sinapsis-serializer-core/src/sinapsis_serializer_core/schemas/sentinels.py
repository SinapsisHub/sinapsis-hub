# -*- coding: utf-8 -*-
"""
Sentinel implementation for Sinapsis-specific use cases.
"""

from sinapsis.sentinels import SinapsisSentinel

SINAPSIS_START_WORKER = SinapsisSentinel("SINAPSIS_START_WORKER")
SINAPSIS_WORKER_READY = SinapsisSentinel("SINAPSIS_WORKER_READY")
SINAPSIS_WORKER_ERROR = SinapsisSentinel("SINAPSIS_WORKER_ERROR")

SINAPSIS_DISK_REF_ID = SinapsisSentinel("SINAPSIS_DISK_REF_ID")
SINAPSIS_SHM_REF_ID = SinapsisSentinel("SINAPSIS_SHM_REF_ID")
SINAPSIS_REDIS_REF_ID = SinapsisSentinel("SINAPSIS_REDIS_REF_ID")
SINAPSIS_CLOUD_REF_ID = SinapsisSentinel("SINAPSIS_CLOUD_REF_ID")
SINAPSIS_RMQ_REF_ID = SinapsisSentinel("SINAPSIS_RMQ_REF_ID")


__all__ = [
    "SINAPSIS_CLOUD_REF_ID",
    "SINAPSIS_DISK_REF_ID",
    "SINAPSIS_REDIS_REF_ID",
    "SINAPSIS_RMQ_REF_ID",
    "SINAPSIS_SHM_REF_ID",
    "SINAPSIS_START_WORKER",
    "SINAPSIS_WORKER_ERROR",
    "SINAPSIS_WORKER_READY",
]
