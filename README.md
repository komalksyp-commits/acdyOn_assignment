Absolutely. Since you want **one final README file you can directly copy-paste**, use the version below. I’ve kept it aligned with your actual project and the assignment requirements, including the live demo and correct repository name.

````markdown
# Acdyon Assignment — JobPulse

Part 1 of the Acdyon Technologies Engineering Assessment:  
**"Getting Data Out of a Platform That Doesn't Want You To"**

## Overview

JobPulse is a resilient job-listing ingestion and discovery application built for Part 1 of the Acdyon Technologies Engineering Assessment. The application pulls real job listings from the publicly documented Arbeitnow Job Board API, validates and normalizes the incoming data, stores it locally in SQLite, and presents the collected listings through a Streamlit dashboard.

The implementation focuses on responsible and resilient data acquisition rather than bypassing protected platforms. It uses bounded pagination, controlled request pacing, request timeouts, retry and exponential backoff, HTTP 429 handling, response validation, safe field extraction, normalization, and duplicate-safe database storage.

The application provides search, filtering, job descriptions, original listing links, progressive loading, statistics, theme support, and interactive UI elements.

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
                    │ progressive loading │
                    └─────────────────────┘
````

The project separates API ingestion, database operations, and presentation so that each part can be understood and tested independently.

## Data Source

**Primary source:** Arbeitnow Job Board API

[https://www.arbeitnow.com/api/job-board-api](https://www.arbeitnow.com/api/job-board-api)

The application uses the publicly documented API to retrieve structured job listings. The API provides job information such as title, company, location, tags, job type, description, and listing URL.

The application uses the API directly instead of browser automation because structured API access is available. This avoids unnecessary browser/fingerprint complexity and allows the implementation to focus on reliable ingestion and data engineering.

Original listing links are preserved where available so users can follow the job back to its source.

## Features

* Public API ingestion using `requests.Session()`
* Paginated fetching
* Configurable `MAX_PAGES` safety cap
* 15-second request timeout
* Controlled 1.5-second pacing between page requests
* Retry with exponential backoff
* HTTP 429 handling with `Retry-After`
* HTTP 5xx transient failure handling
* Response JSON structure validation
* Empty response handling
* Safe handling of missing fields
* Data normalization
* SQLite persistence
* `slug`-based deduplication
* `ON CONFLICT` upsert behaviour
* Search by job title/company
* Location filtering
* Remote-only filtering
* Expandable job descriptions
* Original job listing links
* Progressive "Load More" browsing
* Ingestion statistics
* Streamlit dashboard
* Light/dark theme support
* Responsive interface
* User-facing error handling
* Python logging
* Ingestion smoke test
* Storage tests
* Interactive Easter eggs

## Detection Surface

The assessment asks us to consider the detection surface when extracting data from platforms.

**Headless/browser fingerprints:**
The implementation does not use a headless browser. It uses the `requests` library to communicate with the public REST API, so browser-specific fingerprinting is not part of the ingestion process.

**Request timing:**
Requests are made sequentially with a controlled 1.5-second delay between page fetches. This avoids unnecessary request bursts.

**Headers:**
A custom User-Agent is sent with each request:

```text
AcdyonJobIngestion/1.0
```

This identifies the application making the API request.

**Behavioral patterns:**
The implementation uses bounded, sequential requests rather than aggressive parallel requests. Pagination is limited using `MAX_PAGES`, which prevents unbounded ingestion.

**Rate limiting:**
HTTP 429 responses are handled explicitly. When a `Retry-After` header is provided, the application waits before retrying.

**Important:**
The implementation uses the publicly documented Arbeitnow API and does not attempt to bypass authentication, CAPTCHAs, anti-bot systems, or access controls on protected platforms.

## Ingestion Strategy

The ingestion module (`src/ingestion.py`) uses:

* `requests.Session()` for connection reuse across pages
* A 15-second timeout on every request
* Controlled pacing with a 1.5-second delay between pages
* `MAX_PAGES` as a safety cap to prevent unbounded pagination
* A retry loop with a maximum of 3 attempts for applicable transient failures
* Exponential backoff for transient failures
* `Retry-After` header handling for HTTP 429 responses
* HTTP 5xx retry handling
* JSON structure validation before processing
* Safe handling of missing fields
* Logging at important decision points

The ingestion process is intentionally bounded and sequential so that it remains predictable and avoids unnecessarily aggressive request behaviour.

## Resilience

| Failure mode               | Handling                                            |
| -------------------------- | --------------------------------------------------- |
| Connection error           | Retry up to 3 times with exponential backoff        |
| Request timeout            | Retry up to 3 times with exponential backoff        |
| HTTP 429                   | Parse `Retry-After` when provided, wait, then retry |
| HTTP 5xx                   | Retry transient server failures                     |
| Invalid JSON               | Log the error and stop ingestion                    |
| Missing `data` list        | Validate the response and stop safely               |
| Empty `data`               | Log the condition and stop pagination gracefully    |
| Missing job fields         | Handle fields safely using `.get()`                 |
| Duplicate ingestion        | `ON CONFLICT (slug) DO UPDATE`                      |
| Empty/unavailable database | Database access is handled safely                   |

The goal is to make the ingestion pipeline fail safely and predictably rather than silently continuing with invalid external data.

## Terms / Ethical Boundary

This implementation:

* Uses the publicly documented Arbeitnow Job Board API
* Does not use a live LinkedIn account
* Does not bypass CAPTCHAs
* Does not bypass authentication
* Does not bypass access controls
* Does not attempt to defeat anti-bot systems
* Uses controlled request pacing
* Handles HTTP 429 responses and `Retry-After` when provided
* Uses bounded pagination
* Links back to the original source/listing where available
* Would stop or switch to another explicitly permitted source if access were disallowed

The purpose of this project is to demonstrate responsible data acquisition and engineering practices. It does not attempt to circumvent technical, contractual, or access restrictions imposed by third-party services.

## Tech Stack

* Python 3.13
* `requests`
* Streamlit
* SQLite
* Git
* GitHub

## Project Structure

```text
acdyOn_assignment/
├── .devcontainer/
│   └── devcontainer.json
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
git clone https://github.com/komalksyp-commits/acdyOn_assignment.git

# Enter the project directory
cd acdyOn_assignment

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment on Windows
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the Streamlit application
streamlit run app.py
```

The application runs locally at:

```text
http://localhost:8501
```

## Testing

### Ingestion Smoke Test

The ingestion smoke test makes a real request to the Arbeitnow API and validates the response structure.

```bash
.venv\Scripts\python tests\test_ingestion_smoke.py
```

**Recorded result:** PASS

### Storage Tests

The storage test suite covers database creation, insertion, retrieval, upsert/deduplication, empty lists, empty tags, remote filtering, search filtering, and missing database edge cases.

```bash
.venv\Scripts\python tests\test_storage.py
```

**Recorded result:** 11/11 passed, 0 failed

### End-to-End Verification

A development verification run recorded:

* 176 jobs fetched from page 1
* 176 records stored in SQLite
* 176 jobs retrieved from the database
* 34 "Engineer" search results
* 15 remote jobs
* Streamlit launched successfully with HTTP 200

**Result:** END-TO-END PASS

> The numerical values above are from a development verification run and may change as the public API data changes.

## Running the Application

```bash
streamlit run app.py
```

Click **Fetch Latest Jobs** to retrieve listings and populate the local database. The dashboard can then be used to search, filter, and explore the collected opportunities.

## Key Design Decisions

### Public API instead of browser automation

The application uses the publicly documented Arbeitnow API because it provides structured job data directly. Browser automation was rejected because it would introduce unnecessary browser and fingerprint complexity when structured API access was already available.

### SQLite for persistence

SQLite was chosen because it provides local persistence without requiring a separate database service and is appropriate for the scale of this assessment.

### Bounded pagination

Pagination is intentionally bounded using `MAX_PAGES` so the ingestion process cannot accidentally continue indefinitely.

### Retry and backoff

Transient failures are handled using bounded retries and exponential backoff. HTTP 429 responses use `Retry-After` when available.

### Separate ingestion and storage layers

API communication and database operations are separated from the Streamlit interface to keep the implementation easier to test, understand, and extend.

## Limitations

* Uses one public API source
* No large-scale distributed ingestion
* No multi-source fallback
* SQLite is intended for assessment/demo scale
* Public API schema may change
* Pagination is intentionally bounded
* Ingestion is manually triggered through the application
* No persistent background scheduler
* No production monitoring or alerting infrastructure

These limitations were intentional trade-offs made within the assessment timeframe.

## Future Improvements

With more development time, possible improvements include:

* Additional permitted data sources
* Source-specific ingestion adapters
* Stronger automated schema validation
* Incremental synchronization
* Persistent scheduled ingestion
* Monitoring and metrics
* More comprehensive automated testing
* Production-grade database
* Schema versioning and migrations
* Background ingestion workers
* Production observability and alerting

## Development Notes

AI-assisted tools were used during development for debugging, implementation exploration, UI iteration, documentation refinement, and troubleshooting.

The application was personally run and verified locally. The ingestion and storage workflows were tested, the Streamlit interface was checked manually, Git/deployment issues were resolved during development, and the deployed application was verified before submission.

The engineering decisions and trade-offs are documented separately in `DECISIONS.md`.

## Demo

**Live Demo:**
[https://thejobdashboard.streamlit.app/](https://thejobdashboard.streamlit.app/)

The application is deployed using Streamlit Community Cloud.

## GitHub

**Repository:**
[https://github.com/komalksyp-commits/acdyOn_assignment](https://github.com/komalksyp-commits/acdyOn_assignment)

## Assessment Scope

This project implements **Part 1 — Getting Data Out of a Platform That Doesn't Want You To**.

The implementation intentionally uses a low-risk public job-board API rather than a live LinkedIn, Indeed, Naukri, or Wellfound account. The objective is to demonstrate an end-to-end ingestion pattern while respecting access boundaries and handling practical engineering concerns such as rate limiting, transient failures, validation, normalization, persistence, and duplicate handling.
