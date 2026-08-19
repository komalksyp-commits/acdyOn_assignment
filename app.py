"""
Job Listing Ingestion Dashboard

A Streamlit application that demonstrates fetching job listings from the
Arbeitnow public API, storing them in SQLite, and displaying them with
filters.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

import streamlit as st

# Ensure the project root is importable.
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion import fetch_jobs
from src.storage import get_jobs, upsert_jobs, count_jobs, DEFAULT_DB_PATH

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Job Listing Ingestion Dashboard",
    page_icon="💼",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Sidebar — data source info
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("About this demo")
    st.markdown(
        """
**Data source:** [Arbeitnow](https://www.arbeitnow.com) Job Board API
**Source type:** Public REST API (no auth required)
**Storage:** SQLite (`data/jobs.db`)
**Ingestion:** Rate-limited, paginated, with retry/backoff
        """
    )
    st.divider()
    st.caption(
        "Part 1 of the Acdyon Technologies Engineering Assessment — "
        "'Getting Data Out of a Platform That Doesn't Want You To.'"
    )

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("Job Listing Ingestion Dashboard")
st.markdown(
    "Job listings are collected from the **public [Arbeitnow](https://www.arbeitnow.com) Job Board API**, "
    "normalised, and stored locally in SQLite. Click the button below to fetch the latest listings."
)

# ---------------------------------------------------------------------------
# Ingestion trigger
# ---------------------------------------------------------------------------

st.subheader("Ingest")
col_btn, col_status = st.columns([1, 3])

with col_btn:
    fetch_clicked = st.button("Fetch Latest Jobs", type="primary")

if fetch_clicked:
    with col_status:
        with st.spinner("Fetching jobs from Arbeitnow…"):
            try:
                jobs = fetch_jobs()
                stored = upsert_jobs(jobs)
                st.success(f"Fetched **{len(jobs)}** jobs and stored **{stored}** records.")
            except Exception as exc:
                st.error(f"Ingestion failed: {type(exc).__name__}: {exc}")

st.divider()

# ---------------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------------

st.subheader("Browse stored jobs")

total = count_jobs()
st.caption(f"Total jobs in database: **{total}**")

if total == 0:
    st.info("No jobs in the database yet. Click **Fetch Latest Jobs** above to get started.")
    st.stop()

col_search, col_remote, col_location = st.columns([2, 1, 1])

with col_search:
    search_query = st.text_input("Search by title or company", placeholder="e.g. Python, Acme…")

with col_remote:
    remote_only = st.checkbox("Remote only")

with col_location:
    # Get distinct locations for the filter dropdown.
    all_jobs_for_locations = get_jobs()
    locations = sorted({j["location"] for j in all_jobs_for_locations if j.get("location")})
    selected_location = st.selectbox("Location", ["All"] + locations)

# ---------------------------------------------------------------------------
# Retrieve and filter jobs
# ---------------------------------------------------------------------------

filtered = get_jobs(search=search_query or None, remote_only=remote_only)

if selected_location != "All":
    filtered = [j for j in filtered if j.get("location") == selected_location]

st.caption(f"Showing **{len(filtered)}** of **{total}** jobs")

if not filtered:
    st.warning("No jobs match the current filters.")
    st.stop()

# ---------------------------------------------------------------------------
# Display jobs
# ---------------------------------------------------------------------------

for job in filtered:
    remote_badge = " 🌐 Remote" if job.get("remote") else ""
    created = ""
    if job.get("created_at"):
        try:
            dt = datetime.datetime.fromtimestamp(job["created_at"], tz=datetime.timezone.utc)
            created = dt.strftime("%Y-%m-%d")
        except (OSError, ValueError):
            pass

    header = f"**{job.get('title', 'Untitled')}** — {job.get('company_name', 'Unknown')}{remote_badge}"
    st.markdown(header)

    meta_parts: list[str] = []
    if job.get("location"):
        meta_parts.append(f"📍 {job['location']}")
    if job.get("job_types"):
        meta_parts.append(f"💼 {', '.join(job['job_types'])}")
    if created:
        meta_parts.append(f"📅 {created}")
    if meta_parts:
        st.caption(" · ".join(meta_parts))

    if job.get("tags"):
        st.write(" ".join(f"`{tag}`" for tag in job["tags"]))

    if job.get("url"):
        st.markdown(f"[View original listing]({job['url']})")

    with st.expander("Job description"):
        desc = job.get("description") or "No description available."
        st.markdown(desc)

    st.divider()
