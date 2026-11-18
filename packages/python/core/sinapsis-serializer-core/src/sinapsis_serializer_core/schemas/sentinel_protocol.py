from pydantic import ConfigDict
from pydantic.dataclasses import dataclass
from sinapsis.sentinels import SINAPSIS_EMPTY_CONTAINER, SinapsisSentinel
from sinapsis_contracts.common.sentinels import SINAPSIS_AGENT_FINISHED, SINAPSIS_TEMPLATE_FINISHED

from sinapsis_serializer_core.schemas.sentinels import (
    SINAPSIS_CLOUD_REF_ID,
    SINAPSIS_DISK_REF_ID,
    SINAPSIS_REDIS_REF_ID,
    SINAPSIS_RMQ_REF_ID,
    SINAPSIS_SHM_REF_ID,
    SINAPSIS_START_WORKER,
)


@dataclass(frozen=True, config=ConfigDict(arbitrary_types_allowed=True))
class ProtocolSentinel:
    """Dataclass with the sentinel information"""

    sentinel: SinapsisSentinel
    control_signal: int
    # max_size_limit: int = 0 # not active by default
    # ref_id_or_path: str | None = None


@dataclass(frozen=True)
class SinapsisMsgPackProtocol:
    """
    Extension IDs 1-10 reserved for Control Signals, i.e. when
    we do not need to send entire data containers or similar
    large payloads.

    We keep them under 10 to take advantage of FixExt and send
    small byte payloads, resulting in O(1) ops

    """

    EMPTY_CONTAINER = ProtocolSentinel(SINAPSIS_EMPTY_CONTAINER, 1)  # 0xd4 0x01
    # END_OF_TRANSACTION = ProtocolSentinel(SINAPSIS_END_OF_TRANSACTION, 2)  # 0xd4 0x02
    TEMPLATE_FINISHED = ProtocolSentinel(SINAPSIS_TEMPLATE_FINISHED, 2)
    AGENT_FINISHED = ProtocolSentinel(SINAPSIS_AGENT_FINISHED, 3)

    REDIS_REF = ProtocolSentinel(SINAPSIS_REDIS_REF_ID, 4)
    DISK_REF = ProtocolSentinel(SINAPSIS_DISK_REF_ID, 5)
    CLOUD_REF = ProtocolSentinel(SINAPSIS_CLOUD_REF_ID, 6)
    RMQ_REF = ProtocolSentinel(SINAPSIS_RMQ_REF_ID, 7)
    SHM_REF = ProtocolSentinel(SINAPSIS_SHM_REF_ID, 8)

    # When we simply want to start a worker there is no need
    # to go through the orchestrator???????
    START_WORKER = ProtocolSentinel(SINAPSIS_START_WORKER, 9)

    def signal_to_sentinel(self, signal: int) -> ProtocolSentinel:
        """
        Resolves a raw integer signal to its corresponding ProtocolSentinel definition.

        This method performs a reverse lookup by inspecting the class attributes. It
        is used to identify which protocol (e.g., Redis, RMQ, Disk) is being
        referenced when only the control signal integer is known.

        Args:
            signal: The integer control signal identifier to look up.

        Returns:
            ProtocolSentinel: The matching sentinel object containing protocol
                metadata.

        Raises:
            ValueError: If the provided signal does not match any registered
                ProtocolSentinel on the class.
        """

        for attr in vars(self.__class__).values():
            if isinstance(attr, ProtocolSentinel) and attr.control_signal == signal:
                return attr
        raise ValueError(f"Unknown signal: {signal}")
