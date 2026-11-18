from collections.abc import Callable
from time import perf_counter
from typing import Any

from sinapsis.data_transport import LLMPerformance


def measure_call_latency(function: Callable[..., Any], *args: Any, **kwargs: Any) -> tuple[Any, float]:
    """Execute a synchronous callable and return its result plus wall-clock latency.

    Args:
        function (Callable[..., _ReturnT]): Callable to execute.
        *args (Any): Positional arguments passed to the callable.
        **kwargs (Any): Keyword arguments passed to the callable.

    Returns:
        tuple[_ReturnT, float]: Callable result and elapsed seconds.
    """
    start_time = perf_counter()
    result = function(*args, **kwargs)
    latency_seconds = perf_counter() - start_time
    return result, latency_seconds


def compute_tokens_per_second(
    output_tokens: int | None, latency_seconds: float | None, current_tokens_per_second: float | None = None
) -> float | None:
    """Derive output throughput from token count and latency.

    Args:
        output_tokens (int | None): Generated output token count.
        latency_seconds (float | None): Measured request latency.
        current_tokens_per_second (float | None): Existing throughput value to preserve when inputs are missing.

    Returns:
        float | None: Derived throughput when possible.
    """
    if output_tokens is None:
        return current_tokens_per_second

    if latency_seconds is None or latency_seconds <= 0:
        return None

    return output_tokens / latency_seconds


def build_client_side_performance(
    current_performance: LLMPerformance | None = None,
    latency_seconds: float | None = None,
    output_tokens: int | None = None,
    time_to_first_token: float | None = None,
) -> LLMPerformance | None:
    """Build or update client-side performance metrics for a request.

    This helper is intended for backends that do not expose native per-request
    performance objects. It stores end-to-end wall-clock latency and derives
    output tokens per second when token counts are available.

    Args:
        current_performance (LLMPerformance | None): Existing performance object to update.
        latency_seconds (float | None): End-to-end elapsed request time.
        output_tokens (int | None): Generated output token count.
        time_to_first_token (float | None): Optional first-token latency.

    Returns:
        LLMPerformance | None: Updated performance object when at least one metric is available.
    """
    performance = current_performance or LLMPerformance()

    if time_to_first_token is not None:
        performance.time_to_first_token = time_to_first_token

    if latency_seconds is not None:
        performance.latency_seconds = latency_seconds

    effective_latency = performance.latency_seconds
    performance.tokens_per_second = compute_tokens_per_second(
        output_tokens=output_tokens,
        latency_seconds=effective_latency,
        current_tokens_per_second=performance.tokens_per_second,
    )

    if (
        performance.time_to_first_token is None
        and performance.latency_seconds is None
        and performance.tokens_per_second is None
    ):
        return None

    return performance
