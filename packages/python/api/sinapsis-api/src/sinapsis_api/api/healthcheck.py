import asyncio
import sys

from sinapsis.logging import sinapsis_logger

from sinapsis_api.constants import ControlType

from .routes._common import command, require_success, router_client


async def main() -> None:
    try:
        response = await asyncio.wait_for(router_client.request(command(ControlType.HEALTH)), timeout=5.0)

        _ = require_success(response)

    except Exception as exc:
        sinapsis_logger.error(f"Router health check failed: {exc}")
        sys.exit(1)
    sinapsis_logger.debug("Router health check succeeded")
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
