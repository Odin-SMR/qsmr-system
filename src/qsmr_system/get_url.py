from __future__ import annotations

import json
import time
from urllib.parse import urlparse, urlunparse

import httpx


def enforce_https(url: str) -> str:
    parsed = urlparse(url)

    # No scheme → assume https
    if not parsed.scheme or parsed.scheme == "http":
        parsed = parsed._replace(scheme="https")

    return urlunparse(parsed)


def get_json_with_retry(
    url: str,
    *,
    max_attempts: int = 10,
    initial_delay: float = 1.0,
    max_delay: float = 120.0,
    timeout: float = 30.0,
) -> str | None:
    """
    Fetch JSON from an endpoint with retries and exponential backoff.

    - Retries on network errors, timeouts, and HTTP 5xx
    - Max retries: max_attempts
    - Backoff doubles each time, capped at max_delay
    """
    url = enforce_https(url)
    delay = initial_delay

    with httpx.Client(timeout=timeout) as client:
        for attempt in range(1, max_attempts + 1):
            try:
                resp = client.get(url)
                print(url, resp)
                resp.raise_for_status()

                data = resp.json()
                if "Data" in data:
                    print("v5 API detected")
                    return json.dumps(data["Data"])
                if "Info" in data:
                    print("v4 API detected")
                    return json.dumps(data["Info"])

                print("Unknown API version")
                return json.dumps(data)

            except (
                httpx.TimeoutException,
                httpx.ConnectError,
                httpx.RemoteProtocolError,
                httpx.HTTPStatusError,
            ) as exc:
                # Only retry on 5xx if it's an HTTP error
                if (
                    isinstance(exc, httpx.HTTPStatusError)
                    and exc.response.status_code < 500
                ):
                    raise  # 4xx → caller error, do not retry

                if attempt == max_attempts:
                    raise RuntimeError(f"Failed after {max_attempts} attempts") from exc

                time.sleep(delay)
                delay = min(delay * 2, max_delay)


if __name__ == "__main__":
    data = get_json_with_retry(
        "https://odin-smr.org/rest_api/v5/level1/2/14205733121/Log/"
    )
    print(json.dumps(data, indent=2))
