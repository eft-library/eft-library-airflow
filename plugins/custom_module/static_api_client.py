"""Static JSON generation requests to the public API."""

import time

import requests

# Up to 600 requests/minute per worker, leaving room below the API's
# default 1,000 requests/minute per-IP limit for other traffic.
REQUEST_INTERVAL_SECONDS = 0.1
RATE_LIMIT_WAIT_SECONDS = 65
MAX_RATE_LIMIT_RETRIES = 3
_last_request_at = None


def get_api_response(url, timeout):
    """Space requests and retry only responses rejected by the IP rate limit."""
    global _last_request_at
    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        if _last_request_at is not None:
            time.sleep(max(0, REQUEST_INTERVAL_SECONDS - (time.monotonic() - _last_request_at)))
        _last_request_at = time.monotonic()
        response = requests.get(url, timeout=timeout)
        if response.status_code != 429:
            response.raise_for_status()
            return response
        if attempt == MAX_RATE_LIMIT_RETRIES:
            response.raise_for_status()
        retry_after = response.headers.get("Retry-After")
        try:
            wait_seconds = max(1, float(retry_after))
        except (TypeError, ValueError):
            wait_seconds = RATE_LIMIT_WAIT_SECONDS
        print(f"[static-api] rate limited: {url}; retrying in {wait_seconds}s")
        time.sleep(wait_seconds)
