# DECISIONS.md

Part 1 of the Acdyon Technologies Engineering Assessment

---

## 1. Why this ingestion strategy over the obvious alternative?

The obvious alternative is scraping a protected platform like LinkedIn directly using a headless browser, bypassing anti-bot measures. I chose the Arbeitnow public REST API instead for three reasons:

**Lower operational and legal risk.** LinkedIn's ToS explicitly prohibits scraping. A public API that invites external consumption eliminates that risk entirely. The Arbeitnow API's own metadata states: "This is a free public API for jobs, please do not abuse."

**Demonstrates the same ingestion patterns.** The assessment asks about detection surface, request timing, pacing, rate limiting, and resilience. A public API still requires all of these: pagination, timeout handling, retry/backoff, 429 handling, response validation, and bounded fetching. The engineering discipline is the same; the legal posture is different.

**Real end-to-end data.** Using a permitted source means I could build, test, and demonstrate a complete working pipeline -- ingestion, storage, and UI -- with actual job listings rather than mocked data. This gives a more honest submission.

---

## 2. One trade-off made because of the time limit, and what I would do with a real week

**The trade-off:** I used one public API and SQLite instead of building a multi-source, production-scale ingestion platform. This limits the demo to a single source and a simple local database.

**With a real week, I would:**

- Add 2-3 additional permitted sources (e.g. RemoteOK, Jobicy) with source-specific adapters
- Implement a scheduler for periodic automatic ingestion
- Add structured logging with metrics (ingestion counts, latency, error rates)
- Use PostgreSQL or similar for production-grade storage
- Write comprehensive automated tests including integration tests with a local mock server
- Add schema versioning so API changes are detected early
- Implement monitoring/alerting for rate-limit breaches and ingestion failures
- Add stronger input validation (e.g. max description length, required field checks)

---

## 3. Where I used AI and what I personally verified or changed

**AI was used for:**

- Project scaffolding (directory structure, .gitignore)
- Implementation suggestions for ingestion and storage modules
- Code review and debugging (e.g. connection cleanup, 429 handling)
- Documentation drafting (README, DECISIONS)

**I personally verified and changed:**

- Confirmed the Arbeitnow API is publicly accessible (HTTP 200, no auth required)
- Verified actual response structure: 176 jobs, 10 fields, pagination links
- Checked rate-limit headers (`x-ratelimit-limit: 50`)
- Ran the ingestion smoke test and confirmed real data returned
- Ran all 11 storage tests and confirmed they pass
- Tested Streamlit launches successfully (HTTP 200)
- Performed end-to-end verification: 176 jobs fetched, stored, and retrieved
- Identified and fixed a security issue: removed `unsafe_allow_html=True` from job description rendering
- Fixed a connection cleanup issue: added `try/finally` to ensure SQLite connections close on exceptions
- Fixed the empty-list upsert path to create the database before returning
- Reviewed every design decision against the actual API behaviour
- Ensured all claims in documentation match verified results

I can explain every line of the submitted code.

---

*Generated as part of the Acdyon Technologies Engineering Assessment.*
