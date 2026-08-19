# Engineering Decisions — JobPulse

## 1. Approach and Source Selection

I chose Part 1 of the assessment and implemented JobPulse as a job-listing ingestion and discovery application. I used the publicly documented Arbeitnow Job Board API as the live source rather than automating a protected platform such as LinkedIn. This was an intentional decision because the assessment explicitly permits a low-risk public job-board API, while still allowing me to demonstrate the ingestion, detection-surface, resilience, and ethical-boundary problems the task is testing.

The obvious alternative was Selenium/Playwright-based browser scraping. I rejected it because browser automation would add unnecessary browser/fingerprint complexity when structured API access was already available. It would also move the implementation closer to CAPTCHA, authentication, and anti-bot restrictions that I deliberately chose not to circumvent.

## 2. Architecture

I separated the system into three responsibilities: `src/ingestion.py` handles API communication and normalization, `src/storage.py` handles SQLite persistence and querying, and `app.py` provides the Streamlit interface. This separation makes the ingestion and storage logic independently testable and keeps the UI from being tightly coupled to the external API.

The flow is:

`Arbeitnow API → Ingestion → Validation/Normalization → SQLite → Streamlit`

I chose SQLite because it provides simple persistent storage without requiring a separate database service and is appropriate for the assessment/demo scale.

## 3. Ingestion Strategy

The ingestion layer uses `requests.Session()` for connection reuse, a 15-second request timeout, sequential page fetching, 1.5-second pacing between pages, and a `MAX_PAGES` safety cap to prevent unbounded ingestion.

Transient failures are handled with bounded retries and exponential backoff. HTTP 429 responses are handled using `Retry-After` when available, and applicable HTTP 5xx responses are retried. Responses are validated before processing, empty `data` results stop pagination gracefully, and missing fields are handled safely during normalization.

I intentionally chose bounded sequential ingestion rather than aggressive parallel requests because predictable and responsible API behaviour was more important than maximizing throughput for this assessment.

## 4. Detection Surface and Resilience

I considered request timing, HTTP headers, browser/headless fingerprints, sequential versus parallel behaviour, pagination, and rate limiting. The implementation does not use a headless browser; it communicates with the public API using `requests` and identifies itself with a custom User-Agent.

The pipeline is designed to fail safely rather than silently: invalid responses stop ingestion, empty pages terminate pagination, transient failures are retried, rate limits are respected through 429/`Retry-After` handling, and duplicate records are handled using SQLite upsert behaviour based on the job slug.

If the primary source became unavailable or disallowed access, my fallback would be to stop using it or switch to another explicitly permitted source rather than attempt to bypass the restriction. I did not implement multi-source fallback within the assessment timeframe.

## 5. Data and Storage Decisions

Raw API responses are normalized into a consistent internal job representation before persistence. SQLite uses upsert/deduplication behaviour so repeated ingestion does not unnecessarily create duplicate jobs.

The dashboard then operates on the locally stored data and provides search, location filtering, remote filtering, expandable descriptions, original listing links, progressive loading, statistics, and theme support.

I kept ingestion manually triggered rather than adding a persistent scheduler. This reduced deployment complexity and kept the implementation focused on the assessment's core ingestion problem.

## 6. Testing and Verification

I created a real API ingestion smoke test and a storage test suite covering schema creation, insertion, retrieval, upsert/deduplication, empty data, empty tags, search, remote filtering, and missing-database edge cases. The recorded storage result was 11/11 tests passed.

I also performed an end-to-end verification covering API fetch → SQLite storage → retrieval → search/filtering → Streamlit. A development verification run recorded 176 jobs fetched from page 1, 176 stored/retrieved records, 34 "Engineer" search results, and 15 remote jobs. These are verification snapshots and can change as the public API data changes.

## 7. Time-Limit Trade-offs

Under the assessment time limit, I prioritized a complete working pipeline over production-scale infrastructure. I deliberately did not implement distributed workers, multiple source adapters, persistent scheduling, production monitoring, or a production database.

With a real week, I would add additional permitted sources through source-specific adapters, incremental synchronization, stronger schema validation, scheduled ingestion, monitoring/metrics, broader automated testing, and a production database such as PostgreSQL.

## 8. Ethical Boundary

I did not use a live LinkedIn account and did not bypass authentication, CAPTCHAs, anti-bot systems, or access controls. I used the permitted public API, bounded requests, controlled pacing, and rate-limit handling. If access were restricted, I would stop or use an explicitly permitted alternative rather than circumvent the restriction.

## 9. AI-Assisted Development

AI tools were used during development for debugging, implementation exploration, UI iteration, documentation refinement, and troubleshooting. I personally ran the application, executed the tests, reviewed and modified the generated code, verified the ingestion/storage workflow, tested the interface, resolved local Git/deployment issues, and verified the deployed application. I understand the submitted implementation and can explain the decisions and code during the follow-up discussion.

## 10. Bonus / UI Decisions

I added small hidden interactive Easter eggs as an optional bonus. They are intentionally separate from the core ingestion functionality and do not affect data collection, storage, or search.

The final application was deployed as a Streamlit application and manually verified at:

https://thejobdashboard.streamlit.app/