"""
Arbeitnow job board ingestion module.

Fetches job listings from the Arbeitnow public API with pagination,
rate-limit awareness, retry/backoff, and response validation.
"""

from __future__ import annotations

import logging
import time
from typing import Any

import requests

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

API_URL: str = "https://www.arbeitnow.com/api/job-board-api"
REQUEST_TIMEOUT: int = 15  # seconds
REQUEST_DELAY: float = 1.5  # seconds between requests (pacing)
MAX_PAGES: int = 5  # safety cap to avoid unbounded fetching
MAX_RETRIES: int = 3  # retries on transient failures
BACKOFF_BASE: float = 2.0  # exponential backoff base

# Known fields we care about from the Arbeitnow API.
KNOWN_FIELDS: tuple[str, ...] = (
    "slug",
    "company_name",
    "title",
    "description",
    "remote",
    "url",
    "tags",
    "job_types",
    "location",
    "created_at",
)


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

def _normalize_job(raw: dict[str, Any]) -> dict[str, Any]:
    """Return a flat dict with only the known fields, safe for missing keys."""
    return {field: raw.get(field) for field in KNOWN_FIELDS}


# ---------------------------------------------------------------------------
# Single-page fetch
# ---------------------------------------------------------------------------

def _parse_retry_after(header_value: str | None, attempt: int) -> float:
    """Parse a Retry-After header value into seconds.

    If the header is missing or non-numeric, fall back to exponential backoff.
    """
    if header_value is not None:
        try:
            return max(float(header_value), 0.0)
        except (ValueError, TypeError):
            pass
    return BACKOFF_BASE ** attempt


def _fetch_page(
    session: requests.Session,
    url: str,
    *,
    timeout: int = REQUEST_TIMEOUT,
) -> dict[str, Any]:
    """Fetch a single page, validate structure, return parsed JSON dict.

    Raises
    ------
    ValueError
        If the response is not valid JSON or lacks the expected structure.
    requests.HTTPError
        On HTTP errors (callers decide which are retryable).
    requests.RequestException
        On connection / timeout errors.
    """
    response = session.get(url, timeout=timeout)
    response.raise_for_status()

    body: Any = response.json()

    if not isinstance(body, dict):
        raise ValueError(f"Expected JSON object, got {type(body).__name__}")

    data = body.get("data")
    if not isinstance(data, list):
        raise ValueError(f"Expected 'data' to be a list, got {type(data).__name__}")

    return body


# ---------------------------------------------------------------------------
# Public ingestion function
# ---------------------------------------------------------------------------

def fetch_jobs(
    *,
    max_pages: int = MAX_PAGES,
    delay: float = REQUEST_DELAY,
    timeout: int = REQUEST_TIMEOUT,
) -> list[dict[str, Any]]:
    """Fetch job listings from the Arbeitnow API across multiple pages.

    Parameters
    ----------
    max_pages:
        Upper bound on how many pages to request (safety limit).
    delay:
        Seconds to sleep between successive requests (rate-limit pacing).
    timeout:
        HTTP request timeout in seconds.

    Returns
    -------
    list[dict[str, Any]]
        A list of normalised job dictionaries.
    """
    all_jobs: list[dict[str, Any]] = []
    session = requests.Session()
    session.headers.update({"User-Agent": "AcdyonJobIngestion/1.0"})

    next_url: str | None = API_URL
    page_num = 0

    while next_url is not None and page_num < max_pages:
        page_num += 1
        logger.info("Fetching page %d: %s", page_num, next_url)

        body: dict[str, Any] | None = None

        # Retry loop for transient failures.
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                body = _fetch_page(session, next_url, timeout=timeout)
                break  # success – exit retry loop
            except requests.ConnectionError as exc:
                wait = BACKOFF_BASE ** attempt
                logger.warning(
                    "Connection error on page %d (attempt %d/%d), "
                    "retrying in %.1fs: %s",
                    page_num, attempt, MAX_RETRIES, wait, exc,
                )
                time.sleep(wait)
            except requests.Timeout as exc:
                wait = BACKOFF_BASE ** attempt
                logger.warning(
                    "Timeout on page %d (attempt %d/%d), "
                    "retrying in %.1fs: %s",
                    page_num, attempt, MAX_RETRIES, wait, exc,
                )
                time.sleep(wait)
            except requests.HTTPError as exc:
                status = getattr(exc.response, "status_code", None)
                if status == 429:
                    retry_after = (
                        exc.response.headers.get("Retry-After")
                        if exc.response is not None
                        else None
                    )
                    wait = _parse_retry_after(retry_after, attempt)
                    logger.warning(
                        "HTTP 429 on page %d (attempt %d/%d), "
                        "retrying in %.1fs",
                        page_num, attempt, MAX_RETRIES, wait,
                    )
                    time.sleep(wait)
                elif status is not None and 500 <= status < 600:
                    wait = BACKOFF_BASE ** attempt
                    logger.warning(
                        "HTTP %d on page %d (attempt %d/%d), "
                        "retrying in %.1fs",
                        status, page_num, attempt, MAX_RETRIES, wait,
                    )
                    time.sleep(wait)
                else:
                    logger.error("Non-retryable HTTP error: %s", exc)
                    raise
            except ValueError as exc:
                logger.error("Invalid response structure: %s", exc)
                raise

        if body is None:
            logger.error(
                "Failed to fetch page %d after %d attempts – stopping.",
                page_num, MAX_RETRIES,
            )
            break

        # Extract and normalise jobs from this page.
        raw_jobs: list[dict[str, Any]] = body["data"]

        if not raw_jobs:
            logger.info("Page %d returned empty data – stopping.", page_num)
            break

        for raw in raw_jobs:
            all_jobs.append(_normalize_job(raw))

        logger.info(
            "Page %d: got %d jobs (total so far: %d)",
            page_num, len(raw_jobs), len(all_jobs),
        )

        # Determine next page URL.
        next_url = body.get("links", {}).get("next")

        # Pace requests (skip delay after the final page).
        if next_url is not None and page_num < max_pages:
            time.sleep(delay)

    logger.info(
        "Ingestion complete – %d jobs across %d page(s).",
        len(all_jobs), page_num,
    )
    return all_jobs
