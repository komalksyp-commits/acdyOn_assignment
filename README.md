# Acdyon Assignment — JobPulse

Part 1 of the Acdyon Technologies Engineering Assessment:  
**"Getting Data Out of a Platform That Doesn't Want You To"**

## Overview

This project demonstrates a resilient job-listing ingestion pipeline that pulls real job data from a public API, normalises it, stores it locally in SQLite, and presents it through a Streamlit dashboard. The implementation prioritises responsible ingestion practices including rate-limiting, bounded pagination, retry and exponential backoff, response validation, duplicate-safe storage, and clear ethical boundaries. The application separates the ingestion, storage, and presentation layers so that the system remains understandable, testable, and straightforward to extend.

JobPulse provides a practical workflow for fetching fresh job listings, storing them locally, and allowing users to search, filter, and explore the collected opportunities through a responsive dashboard.

## Architecture

```text
                    ┌─────────────────────┐
                    │  Arbeitnow Job API  │
                    │   Public REST API   │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Ingestion Layer   │
                    │ pagination / retry  │
                    │ pacing / validation │
                    │ rate-limit handling │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    SQLite Store     │
                    │ upsert / dedupe     │
                    │ search / filtering  │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Streamlit App      │
                    │ search / filters    │
                    │ job details / UI    │
                    │ load more / themes  │
                    └─────────────────────┘



## Data Source

Primary source: Arbeitnow Job Board API

Public REST API
No authentication required
Returns JSON with job listings
Includes information such as title, company, location, tags, job type, description, and listing URL
Supports paginated results
Original job listing links are preserved where available

The application uses the public API rather than browser automation because the API provides structured job data directly. This keeps the implementation focused on responsible ingestion, normalization, storage, and presentation rather than attempting to extract data from a protected website interface.

## Features
- Public API ingestion with `requests.Session()`
- Paginated fetching with configurable `MAX_PAGES` safety cap
- Request timeout handling (15 seconds)
- Controlled request pacing (1.5 seconds between pages)
- Retry with exponential backoff
- HTTP 429 rate-limit handling with `Retry-After` support
- HTTP 5xx transient failure retry
- Response JSON structure validation
- Empty `data` handling without crashing
- Safe field extraction
- Normalised job dictionaries
- SQLite storage with `INSERT ... ON CONFLICT` upsert
- `slug`-based deduplication
- Search filter for title/company
- Remote-only filter
- Location filter
- Expandable job descriptions
- Link to original job listing
- Progressive Load More browsing
- Ingestion statistics
- Streamlit dashboard with sidebar information
- Light/dark theme support
- Responsive interface
- User-facing error handling
- Python logging
- Ingestion smoke test
- Storage tests
- Small hidden Easter eggs for additional interaction

##Engineering Highlights

The implementation focuses on reliability and responsible ingestion rather than simply fetching and displaying data. API requests use connection reuse, explicit timeouts, controlled pacing, bounded pagination, retry handling, exponential backoff, and rate-limit awareness. Incoming responses are validated and normalized before being persisted in SQLite, while upsert behavior prevents repeated ingestion from unnecessarily creating duplicate records. The application separates ingestion, storage, and presentation into dedicated components and provides a practical Streamlit interface with search, filtering, progressive loading, job descriptions, original listing links, and theme support. The system was intentionally kept simple enough to understand and test within the assessment timeframe while leaving clear extension points for multiple sources, scheduling, monitoring, stronger validation, and production storage.

## Detection Surface

The assessment asks us to consider the detection surface when extracting data from platforms:

**Headless/browser fingerprints:** This implementation does not use a headless browser. It uses the `requests` library to call a public REST API, so browser fingerprinting is not relevant.

**Request timing:** Requests are paced at 1.5 seconds between page fetches. This provides controlled request behaviour and avoids unnecessary request bursts.

**Headers:** A custom `User-Agent` header (`AcdyonJobIngestion/1.0`) is sent with each request to identify the application making the request.

**Behavioral patterns:** The implementation makes bounded, sequential page requests rather than aggressive parallel scraping. The `MAX_PAGES` cap (default: 5) prevents unbounded pagination.

**Rate limiting:** HTTP 429 responses are handled using the `Retry-After` header when provided, followed by controlled retry behaviour and exponential backoff.

**Important:** This implementation uses the publicly documented Arbeitnow API. It does not attempt to bypass anti-bot systems, CAPTCHAs, authentication, or access controls on protected platforms.


## Ingestion Strategy

The ingestion module (`src/ingestion.py`) uses:

* `requests.Session()` for connection reuse across pages
* A 15-second timeout on every request
* Controlled pacing (1.5s delay between pages)
* `MAX_PAGES` safety cap to prevent unbounded pagination
* A retry loop (3 attempts) with exponential backoff for transient failures
* `Retry-After` header parsing for HTTP 429 responses
* JSON structure validation before processing
* Logging at every decision point


## Resilience

| Failure mode | Handling |
|---|---|
| Connection error | Retry up to 3 times with exponential backoff |
| Request timeout | Retry up to 3 times with exponential backoff |
| HTTP 429 | Parse `Retry-After` when provided, wait, then retry |
| HTTP 5xx | Retry transient server failures up to 3 times |
| Invalid JSON | Log the error and stop ingestion |
| Missing `data` list | Validate the response and stop ingestion safely |
| Empty `data` | Log the condition and stop pagination gracefully |
| Missing job fields | Fields are handled safely using `.get()` |
| Duplicate ingestion | `ON CONFLICT (slug) DO UPDATE` updates the existing record |
| Empty or unavailable database | Database access is handled safely without crashing |

## Terms / Ethical Boundary

This implementation:

- Uses the publicly documented Arbeitnow Job Board API
- Does not use a live LinkedIn account
- Does not bypass CAPTCHAs
- Does not bypass authentication
- Does not bypass access controls
- Does not attempt to defeat anti-bot systems
- Uses controlled request pacing
- Handles HTTP 429 responses and `Retry-After` when provided
- Uses bounded pagination
- Links back to the original source/listing where available
- Would stop rather than attempt to circumvent a restriction if access were disallowed

The purpose of this project is to demonstrate responsible data acquisition and engineering practices. It does not attempt to circumvent technical, contractual, or access restrictions imposed by third-party services.

## Tech Stack
- Python 3.13
- requests
- Streamlit
- SQLite (built-in)
- Git / GitHub

## Project Structure

```text
acdyOn_assignment/
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

## Setup

```bash
# Clone the repository
git clone https://github.com/komalksyp-commits/acdyOn_assignment.git
cd acdyOn_assignment

# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit application
streamlit run app.py


```
# Clone the repository
git clone https://github.com/komalksyp-commits/acdyOn_assignment.git
cd acdyOn_assignment

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\activate        # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit application
streamlit run app.py

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

**Live Demo:-** https://thejobdashboard.streamlit.app/

## GitHub

**Repository:** [https://github.com/komalksyp-commits/acdyOn_assignment](https://github.com/komalksyp-commits/acdyOn_assignment)
