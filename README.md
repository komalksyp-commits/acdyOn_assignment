# Acdyon Assignment

Part 1 of the Acdyon Technologies Engineering Assessment:
**"Getting Data Out of a Platform That Doesn't Want You To"**

## Overview

This project demonstrates a resilient job-listing ingestion pipeline that pulls real job data from a public API, normalises it, stores it locally in SQLite, and presents it through a Streamlit dashboard. The implementation prioritises responsible ingestion practices: rate-limiting, bounded pagination, retry/backoff, response validation, and ethical boundaries.

## Architecture

```
Arbeitnow Job Board API (public REST, no auth)
        |
        v
  src/ingestion.py
        |
        v
  validation / pagination / pacing / retry / backoff
        |
        v
  src/storage.py
        |
        v
  SQLite  (data/jobs.db)
        |
        v
  app.py / Streamlit
```

## Data Source

**Primary source:** [Arbeitnow Job Board API](https://www.arbeitnow.com/api/job-board-api)

- Public REST API, no authentication required
- Returns JSON with job listings (title, company, location, tags, etc.)
- Pagination via `?page=N` parameter
- Rate limit: 50 requests per window
- Data refreshed hourly by Arbeitnow
- [Link back to Arbeitnow](https://www.arbeitnow.com) (appreciated per their API terms)

## Features

- Public API ingestion with `requests.Session()`
- Paginated fetching with configurable `MAX_PAGES` safety cap
- Request timeout handling (15s)
- Controlled request pacing (1.5s between pages)
- Retry with exponential backoff (3 attempts)
- HTTP 429 rate-limit handling with `Retry-After` support
- HTTP 5xx transient failure retry
- Response JSON structure validation
- Empty `data` handling without crashing
- Safe field extraction (missing fields become `None`)
- Normalised job dictionaries
- SQLite storage with `INSERT ... ON CONFLICT` upsert
- `slug`-based deduplication
- Search filter (title/company)
- Remote-only filter
- Location filter
- Expandable job descriptions
- Link to original job listing
- Streamlit dashboard with sidebar info
- Error handling with user-facing messages
- Python logging throughout
- Ingestion smoke test (1 API call)
- Storage tests (11 assertions)

## Detection Surface

The assessment asks us to consider the detection surface when extracting data from platforms:

**Headless/browser fingerprints:** This implementation does not use a headless browser. It uses the `requests` library to call a public REST API, so browser fingerprinting is not relevant.

**Request timing:** Requests are paced at 1.5 seconds between page fetches. This is conservative and avoids triggering rate limits.

**Headers:** A custom `User-Agent` header (`AcdyonJobIngestion/1.0`) is sent with each request. The API does not enforce header-based restrictions.

**Behavioral patterns:** The implementation makes bounded, sequential page requests rather than aggressive parallel scraping. The `MAX_PAGES` cap (default: 5) prevents unbounded pagination.

**Rate limiting:** The Arbeitnow API enforces a limit of 50 requests per window. The implementation respects `Retry-After` headers on HTTP 429 responses and uses exponential backoff.

**Important:** This implementation uses a public API that explicitly permits external access. It does not attempt to bypass anti-bot systems, CAPTCHAs, or access controls on protected platforms.

## Ingestion Strategy

The ingestion module (`src/ingestion.py`) uses:

- `requests.Session()` for connection reuse across pages
- A 15-second timeout on every request
- Controlled pacing (1.5s delay between pages)
- `MAX_PAGES` safety cap to prevent unbounded pagination
- A retry loop (3 attempts) with exponential backoff for transient failures
- `Retry-After` header parsing for HTTP 429 responses
- JSON structure validation before processing
- Logging at every decision point

## Resilience

| Failure mode | Handling |
|---|---|
| Connection error | Retry up to 3 times with backoff (2s, 4s, 8s) |
| Request timeout | Retry up to 3 times with backoff |
| HTTP 429 | Parse `Retry-After`, sleep, retry |
| HTTP 5xx | Retry up to 3 times with backoff |
| Invalid JSON | Log error, raise, stop ingestion |
| Missing `data` list | Log error, raise, stop ingestion |
| Empty `data` | Log info, stop pagination gracefully |
| Missing job fields | Fields default to `None` via `.get()` |
| Duplicate ingestion | `ON CONFLICT (slug) DO UPDATE` updates in place |
| Database not found | `get_jobs` returns empty list, `count_jobs` returns 0 |

## Terms / Ethical Boundary

This implementation:

- Uses a public API that explicitly permits external access
- Does not use a live LinkedIn account
- Does not bypass CAPTCHAs
- Does not bypass authentication
- Does not bypass access controls
- Uses responsible request pacing
- Respects rate limits and `Retry-After` headers
- Links back to Arbeitnow as their terms appreciate
- Would stop rather than circumvent a restriction if a source disallowed access

## Tech Stack

- Python 3.13
- requests
- Streamlit
- SQLite (built-in)
- Git / GitHub

## Project Structure

```
acedyon_assignment/
├── src/
│   ├── __init__.py
│   ├── ingestion.py
│   └── storage.py
├── tests/
│   ├── test_ingestion_smoke.py
│   └── test_storage.py
├── app.py
├── requirements.txt
├── .gitignore
├── README.md
└── DECISIONS.md
```

## Setup

```bash
# Clone the repository
git clone https://github.com/komalksyp-commits/acedyon_assignment.git
cd acedyon_assignment

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit application
streamlit run app.py
```

## Testing

### Ingestion Smoke Test

Fetches page 1 from the Arbeitnow API and validates the response structure:

```bash
.venv\Scripts\python tests\test_ingestion_smoke.py
```

**Result:** PASS

### Storage Tests

11 tests covering schema creation, insert, retrieve, upsert/dedup, empty lists, empty tags, remote filter, search filter, and missing database edge cases:

```bash
.venv\Scripts\python tests\test_storage.py
```

**Result:** 11/11 passed, 0 failed

### End-to-End Verification

Verified programmatically:

- 176 jobs fetched from page 1
- 176 records stored in SQLite
- 176 jobs retrieved from database
- 34 "Engineer" search results
- 15 remote jobs
- Streamlit launches successfully (HTTP 200)

**Result:** END-TO-END PASS

## Running the Application

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`. Click **Fetch Latest Jobs** to ingest listings, then browse and filter them in the dashboard.

## Limitations

- Uses only one public API source (Arbeitnow)
- No large-scale distributed ingestion
- No multi-source fallback implemented
- SQLite is appropriate for this assessment/demo scale
- Public API schema may change without notice
- Bounded pagination (`MAX_PAGES=5`) is intentional for safety
- No persistent scheduling (ingestion is manual via button click)

## Future Improvements

With more time, the following could be added:

- Additional permitted data sources
- Stronger automated schema validation
- Persistent ingestion scheduling (e.g. cron, Airflow)
- Monitoring and metrics (ingestion success rates, latency)
- More comprehensive automated test suite
- Production-grade database
- Source-specific adapters for multiple APIs
- Schema versioning and migration

## Demo

**Live Demo:** TODO -- deployment pending

## GitHub

**Repository:** [https://github.com/komalksyp-commits/acedyon_assignment](https://github.com/komalksyp-commits/acedyon_assignment)
