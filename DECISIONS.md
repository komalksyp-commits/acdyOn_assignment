Yes. Since you're short on time, **leave the README as it is and focus on `DECISIONS.md`**. This is actually the better place to explain the detailed engineering choices, trade-offs, problems encountered, testing, UI decisions, and why you chose each approach.

Below is a **complete `DECISIONS.md`** you can copy-paste. I have kept it grounded in the work we've actually discussed rather than inventing extra features or results.

````markdown
# Engineering Decisions — JobPulse

## 1. Purpose

This document records the engineering decisions, implementation trade-offs, testing decisions, limitations, and development considerations made while building JobPulse for Part 1 of the Acdyon Technologies Engineering Assessment.

The goal was not only to build a working job dashboard, but to demonstrate how data can be acquired from a public platform responsibly, transformed into a consistent internal representation, persisted locally, and exposed through a usable interface.

The implementation prioritises:

- Responsible API usage
- Controlled request behaviour
- Resilience to transient failures
- Bounded ingestion
- Data validation
- Duplicate-safe storage
- Separation of concerns
- Testability
- A simple but usable user interface
- Clear ethical boundaries

---

# 2. Assessment Interpretation

The assessment asks for data to be obtained from a platform that may have restrictions around automated extraction.

Instead of attempting to bypass a protected website, CAPTCHA, authentication system, or anti-bot mechanism, the implementation uses the publicly documented Arbeitnow Job Board API.

This was an intentional engineering decision.

The API provides structured job information directly, which avoids unnecessary browser automation and allows the implementation to focus on the engineering problems that are relevant to the assessment:

1. Getting data reliably
2. Handling pagination
3. Handling transient failures
4. Respecting controlled request behaviour
5. Validating external data
6. Normalising records
7. Persisting data
8. Avoiding duplicates
9. Searching and filtering the collected data
10. Providing a usable interface

The implementation does not attempt to circumvent access restrictions on protected platforms.

---

# 3. High-Level Architecture Decision

The application was divided into three primary layers:

```text
Arbeitnow API
      |
      v
Ingestion Layer
(src/ingestion.py)
      |
      v
Storage Layer
(src/storage.py)
      |
      v
SQLite
      |
      v
Streamlit Application
(app.py)
````

This separation was chosen so that API communication, persistence, and presentation would not be tightly coupled.

### Ingestion Layer

Responsible for:

* Making API requests
* Pagination
* Request pacing
* Retry handling
* HTTP 429 handling
* Response validation
* Normalisation
* Logging

### Storage Layer

Responsible for:

* SQLite database access
* Schema management
* Insert/upsert operations
* Retrieval
* Search
* Filtering
* Duplicate handling

### Application Layer

Responsible for:

* Streamlit interface
* User interaction
* Fetching latest jobs
* Search
* Location filtering
* Remote filtering
* Job display
* Job descriptions
* Original listing links
* Progressive loading
* Theme/interface behaviour

This structure makes the project easier to reason about and allows individual parts to be tested separately.

---

# 4. Why the Arbeitnow API Was Chosen

The project uses the publicly documented Arbeitnow Job Board API as its primary data source.

The API was selected because it provides structured job data without requiring browser automation.

The response contains job information such as:

* Job title
* Company
* Location
* Tags
* Job type
* Description
* Listing URL
* Other job metadata

Using an API also avoids unnecessary interaction with a protected website interface.

The decision was therefore both technically practical and aligned with the ethical requirements of the assessment.

---

# 5. Why Browser Automation Was Not Used

A headless browser such as Selenium or Playwright was not used for ingestion.

The reason was simple: the required data was already available through a public REST API.

Using browser automation would have introduced unnecessary complexity, including:

* Browser lifecycle management
* Page rendering
* JavaScript execution
* Browser fingerprints
* More complicated failure modes
* Higher resource usage
* Greater request overhead

Since the public API provided structured JSON directly, `requests` was a more appropriate solution.

---

# 6. HTTP Client Decision

The ingestion layer uses:

```python
requests.Session()
```

A `Session` was selected instead of making completely independent requests because it allows connection reuse and keeps the HTTP interaction straightforward.

The implementation also uses an explicit timeout.

The timeout prevents a request from waiting indefinitely if the remote service becomes unavailable or stops responding.

The configured timeout is:

```text
15 seconds
```

This provides a clear upper bound for an individual request.

---

# 7. Pagination Decision

The API provides paginated job results.

The ingestion process therefore fetches pages sequentially rather than attempting to retrieve an unlimited amount of data.

A configurable:

```text
MAX_PAGES
```

limit is used.

The default documented value is:

```text
5 pages
```

The purpose of this limit is to prevent accidental unbounded ingestion.

This is especially important when working with an external API because an implementation should not continue requesting pages indefinitely simply because more pages may exist.

Bounded pagination also makes development and testing more predictable.

---

# 8. Request Pacing Decision

Requests are intentionally paced between page fetches.

The configured delay is:

```text
1.5 seconds
```

The purpose is to avoid unnecessary request bursts and maintain controlled request behaviour.

The application does not use aggressive parallel requests for ingestion.

Sequential requests were considered sufficient for the assessment scale.

---

# 9. Retry Strategy

External API requests can fail for temporary reasons.

Examples include:

* Network errors
* Connection failures
* Request timeouts
* Temporary server failures
* HTTP 5xx responses
* HTTP 429 responses

The ingestion layer therefore uses a retry mechanism.

The retry loop allows up to three attempts for applicable transient failures.

Exponential backoff is used so that the application does not immediately repeat a failed request at the same frequency.

The intention is:

```text
Failure
   |
   v
Wait
   |
   v
Retry
   |
   v
Failure again
   |
   v
Longer wait
   |
   v
Retry
```

This is preferable to continuously retrying without a delay.

---

# 10. HTTP 429 Handling

HTTP 429 indicates that the client has made too many requests for the server's current allowance.

The implementation explicitly handles HTTP 429 responses.

When a `Retry-After` header is provided, the ingestion layer reads that value and waits before retrying.

This was chosen instead of blindly retrying immediately.

The implementation therefore treats rate-limit responses as a signal to slow down rather than as an error that should be bypassed.

---

# 11. HTTP 5xx Handling

HTTP 5xx responses can represent temporary server-side failures.

The ingestion layer retries applicable 5xx responses rather than immediately failing the entire ingestion process.

The retry count remains bounded.

This is important because retrying forever could create an uncontrolled request loop.

---

# 12. Response Validation

External API data should not be trusted blindly.

The ingestion layer validates the response structure before attempting to process the records.

The expected JSON response must contain the required data structure.

If the response is invalid or does not contain the expected `data` list, ingestion stops safely rather than continuing with assumptions about the response.

This prevents malformed external data from silently entering the database.

---

# 13. Empty Data Handling

An empty `data` result is treated differently from a malformed response.

An empty page can represent the end of available pagination.

Therefore, when the API returns an empty data collection, the ingestion process stops pagination gracefully.

This prevents unnecessary requests for additional pages.

---

# 14. Missing Field Handling

External APIs can contain records with missing or optional fields.

The ingestion process therefore uses safe field extraction rather than assuming every field will always be present.

For example, dictionary access is performed using `.get()` where appropriate.

This means that missing optional values can be represented safely rather than causing the entire ingestion process to crash.

---

# 15. Data Normalisation

The raw API response is not stored blindly.

The ingestion layer extracts the fields needed by the application and creates normalised job dictionaries.

This creates a consistent internal representation regardless of small differences in individual API records.

Normalisation also keeps the storage layer independent of the exact structure of the external API response.

---

# 16. SQLite Decision

SQLite was selected as the database for this assessment.

Reasons:

* Built into Python
* No separate database server required
* Easy local persistence
* Simple deployment
* Easy testing
* Appropriate for assessment/demo scale
* Sufficient for the number of records handled by the application

A production system at larger scale could use PostgreSQL or another production database, but introducing a separate database service would add unnecessary infrastructure for this assessment.

SQLite therefore provides an appropriate balance between persistence and simplicity.

---

# 17. Duplicate Handling

Repeated ingestion should not create unnecessary duplicate job records.

The database uses the job `slug` as the conflict/deduplication key.

The storage layer uses:

```sql
ON CONFLICT (slug) DO UPDATE
```

This means that when a job with the same slug is ingested again, the existing record can be updated instead of creating another duplicate row.

This makes repeated ingestion safer.

---

# 18. Separation of Storage and Ingestion

The ingestion code does not directly contain all database operations.

Instead:

```text
src/ingestion.py
```

handles external data acquisition, while:

```text
src/storage.py
```

handles persistence.

This separation was intentional.

It means that:

* The ingestion layer can be tested independently.
* The storage layer can be tested independently.
* The Streamlit interface does not need to know API implementation details.
* The database implementation can be changed later without redesigning the entire UI.
* Another permitted data source could potentially be added through another ingestion adapter.

---

# 19. Streamlit Decision

Streamlit was selected for the user interface because the assessment required a practical way to demonstrate the collected data.

It allows the project to provide:

* Search
* Location filtering
* Remote-only filtering
* Job cards/listings
* Job descriptions
* Original listing links
* Ingestion controls
* Statistics
* Progressive loading
* Theme support

without requiring a separate frontend framework and backend server.

This kept the implementation focused on the ingestion and data engineering requirements.

---

# 20. Search Decision

The application provides job search functionality.

Search is intended to make the collected dataset useful rather than simply displaying raw API records.

The search functionality focuses on relevant job information such as:

* Job title
* Company

This provides a simple way for users to find opportunities without needing to inspect every record.

---

# 21. Filtering Decision

The application provides filters for:

* Location
* Remote jobs

These filters were selected because they are directly useful when exploring job listings.

The filters operate on the locally stored/loaded dataset rather than requiring a new external API request for every interaction.

---

# 22. Progressive Loading Decision

The interface uses progressive loading / "Load More" behaviour rather than presenting every job record on the page at once.

This improves usability when the database contains many listings.

It also keeps the interface visually manageable.

The ingestion process and the presentation process are therefore separate:

```text
Fetch many records
        |
        v
Store them
        |
        v
Display a manageable subset
        |
        v
Load more when requested
```

---

# 23. Job Description Decision

Job descriptions are available through expandable UI elements.

This avoids making every job card unnecessarily large.

The user can inspect the description when interested while keeping the main results view compact.

---

# 24. Original Listing Link Decision

Where an original listing URL is available, the application provides a link to the original job posting.

This allows the dashboard to act as a discovery interface rather than pretending to replace the original source.

It also maintains a clear connection between the normalized local record and its source.

---

# 25. Theme/UI Decision

The application includes light/dark theme support and interactive UI elements.

The intention was to make the dashboard feel like a finished application rather than only a technical data table.

The UI was iterated during development to improve:

* Readability
* Navigation
* Visual hierarchy
* Search/filter interaction
* Job presentation
* Theme behaviour
* Interactive elements

---

# 26. Hidden Easter Eggs

Small hidden interactive Easter eggs were intentionally included in the interface as an additional interaction layer.

The purpose was to reward exploration without interfering with the primary job-search functionality.

The Easter eggs are not required for the core functionality of the application.

They were kept separate from the main data pipeline so that they do not affect ingestion, storage, or search behaviour.

---

# 27. Logging Decision

Python logging is used in the ingestion process.

Logging is useful because ingestion involves external dependencies and multiple decision points.

Examples of useful events include:

* Request attempts
* Retry behaviour
* Rate-limit responses
* Validation failures
* Empty pages
* Successful ingestion decisions
* Errors

The objective is to make ingestion behaviour easier to understand during development and troubleshooting.

---

# 28. Error Handling Philosophy

The application follows a fail-safely approach.

The goal is not to hide every error.

Instead, expected failures are handled where possible, while unexpected or invalid conditions are surfaced appropriately.

Examples:

```text
Network failure
    -> retry

Timeout
    -> retry

HTTP 429
    -> respect Retry-After and retry

Temporary 5xx
    -> retry

Invalid response
    -> stop safely

Empty page
    -> stop pagination

Missing optional field
    -> safely handle missing value
```

This makes the behaviour more predictable than allowing every error to propagate directly to the user.

---

# 29. Testing Strategy

Testing was split into multiple levels.

## Ingestion Smoke Test

The ingestion smoke test makes a real API request and validates that the response structure is usable.

The purpose is to verify that the external API can be reached and that the expected response structure is still available.

## Storage Tests

The storage tests cover database behaviour including:

* Schema creation
* Insert
* Retrieve
* Upsert
* Deduplication
* Empty lists
* Empty tags
* Remote filtering
* Search filtering
* Missing database edge cases

The recorded result was:

```text
11/11 passed
```

## End-to-End Verification

The application was also verified across the complete workflow:

```text
API
 ↓
Ingestion
 ↓
SQLite
 ↓
Retrieval
 ↓
Search/filtering
 ↓
Streamlit
```

A recorded verification run included:

* 176 jobs fetched from page 1
* 176 records stored in SQLite
* 176 jobs retrieved from the database
* 34 "Engineer" search results
* 15 remote jobs
* Streamlit successfully launching with HTTP 200

These numbers represent a development verification snapshot and are not treated as permanent API statistics.

---

# 30. Deployment Decision

The application was deployed as a Streamlit application.

Live deployment:

[https://thejobdashboard.streamlit.app/](https://thejobdashboard.streamlit.app/)

The deployment provides an externally accessible demonstration of the completed application.

The local development environment and deployed application are separate concerns: local development was used for implementation and testing, while the deployment provides the evaluator with access to the finished dashboard.

---

# 31. Deployment Issue and Resolution

During development, the local project folder was renamed from:

```text
acedyon_assignment
```

to:

```text
acdyOn_assignment
```

The Git remote was also updated to the correct repository:

```text
https://github.com/komalksyp-commits/acdyOn_assignment.git
```

The repository was verified using:

```bash
git remote -v
```

The final working tree was also verified using:

```bash
git status
```

with the final state showing:

```text
nothing to commit, working tree clean
```

This confirmed that the local repository and remote repository were synchronized at the point of final verification.

---

# 32. Git Workflow Decision

Git was used throughout development to track changes.

The workflow included:

```bash
git status
git add
git commit
git push
```

When the remote repository contained commits that were not present locally, a normal push was rejected.

Instead of overwriting the remote history, the changes were integrated using:

```bash
git pull --rebase origin master
```

After the rebase completed successfully, the changes were pushed again.

This preserved the remote history and avoided using a force push unnecessarily.

---

# 33. Backup File Cleanup

An `app_backup.py` file was temporarily created during development.

It was later deleted because it was not part of the final application.

The deletion was staged and committed separately.

The repository was then synchronized with the remote repository.

The final project structure intentionally contains only the files required for the submitted application and documentation.

---

# 34. Repository Structure Decision

The final repository is structured as:

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
```

This structure keeps source code, tests, application code, and documentation logically separated.

---

# 35. Why No Distributed Architecture Was Used

A distributed ingestion architecture was not implemented.

The assessment scale does not justify introducing:

* Message queues
* Multiple workers
* Distributed schedulers
* Container orchestration
* Complex cloud infrastructure

Adding these components would increase complexity without providing meaningful value for the demonstrated workload.

The implementation therefore uses a simple local architecture while documenting distributed ingestion as a possible future improvement.

---

# 36. Why No Multi-Source Fallback Was Implemented

Only the permitted/public Arbeitnow API was used as the direct source.

A multi-source architecture could improve availability in a production system, but implementing several external sources would require:

* Different schemas
* Source-specific adapters
* Different pagination rules
* Different rate-limit behaviour
* Different failure handling
* Additional normalization logic
* Additional testing

Given the assessment timeframe, a single well-handled source was chosen instead of several incompletely integrated sources.

---

# 37. Why No Persistent Scheduler Was Implemented

The application does not run ingestion continuously in the background.

Ingestion is triggered from the application.

A persistent scheduler such as cron or Airflow could be introduced later.

For this assessment, manual ingestion was considered sufficient because it keeps the deployment simple and avoids introducing background infrastructure.

---

# 38. Why SQLite Is Considered Sufficient

SQLite is not intended to represent the final production database architecture.

It was selected because:

* It requires no external service.
* It is easy to inspect.
* It is easy to test.
* It supports the required operations.
* It is appropriate for the assessment/demo workload.

A production deployment with larger scale or multiple concurrent workers could use PostgreSQL or another managed relational database.

---

# 39. Security and Ethical Boundary

The implementation intentionally avoids techniques designed to circumvent access restrictions.

It does not:

* Use a live LinkedIn account
* Bypass authentication
* Bypass CAPTCHAs
* Defeat anti-bot systems
* Circumvent access controls
* Attempt to hide automated access
* Use browser automation to bypass restrictions

The project uses a publicly documented API and controlled request behaviour.

If a source disallowed access or introduced a restriction, the appropriate engineering response would be to stop or use an explicitly permitted alternative rather than attempting to circumvent the restriction.

---

# 40. Detection Surface Considerations

The assessment specifically requires consideration of the detection surface.

The implementation considered:

### Browser fingerprints

No headless browser is used.

The application communicates through HTTP requests to the public API.

### Request timing

Requests are separated by a controlled 1.5-second delay between page fetches.

### Headers

A custom User-Agent identifies the application:

```text
AcdyonJobIngestion/1.0
```

### Behaviour

Requests are:

* Sequential
* Bounded
* Non-parallel
* Limited by `MAX_PAGES`

### Rate limits

HTTP 429 responses are handled and `Retry-After` is used when provided.

The important design principle is that the implementation responds to restrictions rather than attempting to defeat them.

---

# 41. Data Quality Considerations

The external API is outside the application's control.

Therefore, the application does not assume that:

* Every field is present
* Every listing has identical metadata
* The schema will remain unchanged forever
* Job counts will remain constant
* Search results will remain constant

The ingestion layer validates the response structure and safely handles missing fields.

The README's numerical verification results are therefore treated as a snapshot rather than a permanent property of the system.

---

# 42. Known Limitations

The final implementation intentionally has several limitations:

* Only one public API source is used.
* There is no distributed ingestion.
* There is no multi-source fallback.
* SQLite is intended for assessment/demo scale.
* The external API schema may change.
* Pagination is bounded.
* Ingestion is manually triggered.
* There is no persistent scheduler.
* There is no production monitoring/alerting infrastructure.

These limitations are intentional and are documented rather than hidden.

---

# 43. Future Improvements

If the project were continued beyond the assessment, possible improvements would include:

1. Multiple permitted API sources
2. Source-specific ingestion adapters
3. Stronger schema validation
4. Schema versioning
5. Database migrations
6. Incremental synchronization
7. Caching
8. Persistent scheduled ingestion
9. Background workers
10. Monitoring and metrics
11. Application logging aggregation
12. Alerting
13. Production database infrastructure
14. Expanded automated testing
15. CI/CD
16. Automated deployment checks

These were not implemented simply for the sake of adding complexity because they were outside the immediate assessment requirements.

---

# 44. Assessment-Time Trade-offs

The project was completed under a limited assessment timeframe.

Therefore, decisions were made to maximise:

* Working functionality
* Reliability
* Explainability
* Testability
* Responsible API usage
* Demonstrable engineering decisions

rather than attempting to implement every possible production feature.

The resulting architecture is intentionally simple but provides clear extension points.

---

# 45. What Was Prioritised

The implementation prioritised the following order:

### 1. Obtain real data

A working API integration was necessary before building the dashboard.

### 2. Make ingestion reliable

Timeouts, retries, rate-limit handling, validation, and bounded pagination were implemented before treating the ingestion workflow as complete.

### 3. Persist the data

SQLite was added so that the application did not depend on making an API request for every dashboard interaction.

### 4. Prevent duplicates

Upsert behaviour was introduced so repeated ingestion would not unnecessarily create duplicate job records.

### 5. Build the dashboard

Search, filtering, job descriptions, original links, statistics, and progressive loading were then added.

### 6. Test the system

Smoke testing, storage testing, and end-to-end verification were performed.

### 7. Deploy

The completed Streamlit application was deployed and manually verified.

### 8. Document decisions

The README and this document were prepared to explain not only what was built, but why it was built this way.

---

# 46. AI-Assisted Development Disclosure

AI-assisted tools were used during parts of the development process.

They were used for activities such as:

* Debugging
* Understanding error messages
* Exploring implementation approaches
* Iterating on UI behaviour
* Refining documentation
* Reviewing implementation decisions
* Troubleshooting Git and deployment issues

The use of AI assistance did not change the requirement to execute and verify the application.

The application was run locally, tested against the ingestion and storage workflows, and manually checked before deployment.

The final responsibility for the submitted implementation and its behaviour remains with the developer.

---

# 47. Final Verification

Before submission, the following areas were verified:

* Local Streamlit application launches
* API ingestion works
* Job records can be stored
* Job records can be retrieved
* Search works
* Location filtering works
* Remote filtering works
* Job descriptions can be viewed
* Original listing links are available where provided
* Storage tests pass
* Ingestion smoke test passes
* Streamlit deployment works
* Git repository is synchronized
* Backup file was removed from the final project structure
* README documents the architecture and engineering approach
* DECISIONS.md documents the major implementation decisions

---

# 48. Final Outcome

JobPulse provides a complete demonstration of a responsible job-listing ingestion workflow:

```text
Public API
    ↓
Controlled ingestion
    ↓
Validation
    ↓
Normalization
    ↓
SQLite persistence
    ↓
Search and filtering
    ↓
Streamlit dashboard
    ↓
Live deployment
```

The implementation intentionally avoids bypassing restrictions and instead demonstrates how to work with a permitted public data source while applying practical engineering techniques for resilience, data quality, persistence, testing, and usability.

The main goal of the project was not to build a large production platform, but to demonstrate sound engineering judgement within the assessment constraints.

---

# 49. Final Links

## Live Demo

[https://thejobdashboard.streamlit.app/](https://thejobdashboard.streamlit.app/)

## GitHub Repository

[https://github.com/komalksyp-commits/acdyOn_assignment](https://github.com/komalksyp-commits/acdyOn_assignment)
