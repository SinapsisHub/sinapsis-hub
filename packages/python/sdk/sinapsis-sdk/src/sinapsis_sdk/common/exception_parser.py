import httpx


def get_error_message(response: httpx.Response) -> str:
    """Extract a useful error message from an API response."""
    try:
        data = response.json()
    except ValueError:
        return response.text or f"API request failed with status {response.status_code}"

    if isinstance(data, dict):
        for key in ("message", "error", "detail"):
            value = data.get(key)

            if isinstance(value, str) and value:
                return value

    return f"API request failed with status {response.status_code}"
