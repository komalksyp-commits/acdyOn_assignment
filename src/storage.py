"""
SQLite storage layer for Arbeitnow job listings.

Provides schema creation, upsert insertion, and retrieval of normalised
job records using only the Python standard library sqlite3 module.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_DB_PATH: str = "data/jobs.db"

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """\
CREATE TABLE IF NOT EXISTS jobs (
    slug        TEXT PRIMARY KEY,
    company_name TEXT,
    title       TEXT,
    description TEXT,
    remote      INTEGER,
    url         TEXT,
    tags        TEXT,
    job_types   TEXT,
    location    TEXT,
    created_at  INTEGER
);
"""


# ---------------------------------------------------------------------------
# Connection helper
# ---------------------------------------------------------------------------

def _connect(db_path: str | Path) -> sqlite3.Connection:
    """Open a connection and ensure the parent directory exists."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db(db_path: str | Path = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create the database file (if needed) and the jobs table schema.

    Returns an open connection that the caller is responsible for closing.
    """
    conn = _connect(db_path)
    conn.execute(_SCHEMA_SQL)
    conn.commit()
    logger.info("Database initialised at %s", db_path)
    return conn


def upsert_jobs(
    jobs: list[dict[str, Any]],
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
) -> int:
    """Insert or update a list of normalised job dictionaries.

    Uses SQLite INSERT … ON CONFLICT (slug) DO UPDATE so re-ingesting the
    same listing updates it instead of creating a duplicate row.

    Returns the number of rows affected.
    """
    conn = init_db(db_path)
    try:
        if not jobs:
            return 0

        _UPSERT_SQL = """\
        INSERT INTO jobs (slug, company_name, title, description, remote,
                          url, tags, job_types, location, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT (slug) DO UPDATE SET
            company_name = excluded.company_name,
            title        = excluded.title,
            description  = excluded.description,
            remote       = excluded.remote,
            url          = excluded.url,
            tags         = excluded.tags,
            job_types    = excluded.job_types,
            location     = excluded.location,
            created_at   = excluded.created_at;
        """

        rows: list[tuple[Any, ...]] = []
        for job in jobs:
            rows.append((
                job.get("slug"),
                job.get("company_name"),
                job.get("title"),
                job.get("description"),
                1 if job.get("remote") else 0,
                job.get("url"),
                json.dumps(job.get("tags") or []),
                json.dumps(job.get("job_types") or []),
                job.get("location"),
                job.get("created_at"),
            ))

        conn.executemany(_UPSERT_SQL, rows)
        conn.commit()
        count = len(rows)
        logger.info("Upserted %d job(s) into %s", count, db_path)
        return count
    finally:
        conn.close()


def get_jobs(
    *,
    db_path: str | Path = DEFAULT_DB_PATH,
    search: str | None = None,
    remote_only: bool = False,
) -> list[dict[str, Any]]:
    """Retrieve jobs from the database.

    Parameters
    ----------
    db_path:
        Path to the SQLite database file.
    search:
        Optional case-insensitive substring match against title or company_name.
    remote_only:
        If True, return only remote listings.

    Returns
    -------
    list[dict[str, Any]]
        A list of job dictionaries with tags/job_types parsed from JSON.
    """
    path = Path(db_path)
    if not path.exists():
        logger.warning("Database not found at %s – returning empty list", db_path)
        return []

    conn = _connect(db_path)
    try:
        query = "SELECT * FROM jobs"
        conditions: list[str] = []
        params: list[Any] = []

        if search:
            conditions.append("(title LIKE ? OR company_name LIKE ?)")
            pattern = f"%{search}%"
            params.extend([pattern, pattern])

        if remote_only:
            conditions.append("remote = 1")

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY created_at DESC"

        cursor = conn.execute(query, params)
        rows = cursor.fetchall()
    finally:
        conn.close()

    results: list[dict[str, Any]] = []
    for row in rows:
        results.append({
            "slug": row["slug"],
            "company_name": row["company_name"],
            "title": row["title"],
            "description": row["description"],
            "remote": bool(row["remote"]),
            "url": row["url"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "job_types": json.loads(row["job_types"]) if row["job_types"] else [],
            "location": row["location"],
            "created_at": row["created_at"],
        })

    return results


def count_jobs(*, db_path: str | Path = DEFAULT_DB_PATH) -> int:
    """Return the total number of rows in the jobs table."""
    path = Path(db_path)
    if not path.exists():
        return 0

    conn = _connect(db_path)
    try:
        cursor = conn.execute("SELECT COUNT(*) FROM jobs")
        result = cursor.fetchone()[0]
    finally:
        conn.close()
    return result
