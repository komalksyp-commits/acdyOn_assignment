"""
Tests for src/storage.py

Uses temporary SQLite files so the real data/jobs.db
is never modified during testing.
"""

import sys
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.storage import init_db, upsert_jobs, get_jobs, count_jobs


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SAMPLE_JOBS = [
    {
        "slug": "eng-acme-001",
        "company_name": "Acme Corp",
        "title": "Software Engineer",
        "description": "Build things",
        "remote": True,
        "url": "https://example.com/1",
        "tags": ["Python", "Backend"],
        "job_types": ["Full-time"],
        "location": "Berlin",
        "created_at": 1700000000,
    },
    {
        "slug": "des-blob-002",
        "company_name": "Blob Inc",
        "title": "Designer",
        "description": "Design things",
        "remote": False,
        "url": "https://example.com/2",
        "tags": ["Design"],
        "job_types": ["Contract"],
        "location": "Munich",
        "created_at": 1700001000,
    },
]

_SAMPLE_UPDATED = {
    "slug": "eng-acme-001",
    "company_name": "Acme Corp",
    "title": "Senior Software Engineer",
    "description": "Build great things",
    "remote": True,
    "url": "https://example.com/1-v2",
    "tags": ["Python", "Backend", "Senior"],
    "job_types": ["Full-time"],
    "location": "Berlin",
    "created_at": 1700002000,
}


def _make_temp_db() -> str:
    """Return a path to a temporary file (deleted after tests)."""
    fd, path = tempfile.mkstemp(suffix=".db")
    import os
    os.close(fd)
    return path


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_init_db_creates_file() -> None:
    path = _make_temp_db()
    conn = init_db(path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='jobs'"
    )
    assert cursor.fetchone() is not None, "jobs table was not created"
    conn.close()
    Path(path).unlink(missing_ok=True)
    print("  PASS  test_init_db_creates_file")


def test_upsert_and_retrieve_single_job() -> None:
    path = _make_temp_db()
    count = upsert_jobs(_SAMPLE_JOBS[:1], db_path=path)
    assert count == 1

    jobs = get_jobs(db_path=path)
    assert len(jobs) == 1
    assert jobs[0]["slug"] == "eng-acme-001"
    assert jobs[0]["title"] == "Software Engineer"
    assert jobs[0]["remote"] is True
    assert jobs[0]["tags"] == ["Python", "Backend"]
    assert jobs[0]["job_types"] == ["Full-time"]
    Path(path).unlink(missing_ok=True)
    print("  PASS  test_upsert_and_retrieve_single_job")


def test_upsert_multiple_jobs() -> None:
    path = _make_temp_db()
    count = upsert_jobs(_SAMPLE_JOBS, db_path=path)
    assert count == 2
    assert count_jobs(db_path=path) == 2
    jobs = get_jobs(db_path=path)
    assert len(jobs) == 2
    Path(path).unlink(missing_ok=True)
    print("  PASS  test_upsert_multiple_jobs")


def test_upsert_no_duplicates_on_reingest() -> None:
    path = _make_temp_db()
    upsert_jobs(_SAMPLE_JOBS, db_path=path)
    upsert_jobs(_SAMPLE_JOBS, db_path=path)
    assert count_jobs(db_path=path) == 2, "Duplicate rows created"
    Path(path).unlink(missing_ok=True)
    print("  PASS  test_upsert_no_duplicates_on_reingest")


def test_upsert_updates_on_conflict() -> None:
    path = _make_temp_db()
    upsert_jobs(_SAMPLE_JOBS[:1], db_path=path)

    upsert_jobs([_SAMPLE_UPDATED], db_path=path)
    assert count_jobs(db_path=path) == 1

    jobs = get_jobs(db_path=path)
    assert jobs[0]["title"] == "Senior Software Engineer"
    assert jobs[0]["tags"] == ["Python", "Backend", "Senior"]
    Path(path).unlink(missing_ok=True)
    print("  PASS  test_upsert_updates_on_conflict")


def test_empty_list_upsert() -> None:
    path = _make_temp_db()
    count = upsert_jobs([], db_path=path)
    assert count == 0
    assert count_jobs(db_path=path) == 0
    Path(path).unlink(missing_ok=True)
    print("  PASS  test_empty_list_upsert")


def test_empty_tags_and_job_types() -> None:
    path = _make_temp_db()
    job = {
        "slug": "empty-001",
        "company_name": "X",
        "title": "Y",
        "description": "Z",
        "remote": False,
        "url": "https://example.com",
        "tags": [],
        "job_types": [],
        "location": "Hamburg",
        "created_at": 1700000000,
    }
    upsert_jobs([job], db_path=path)
    jobs = get_jobs(db_path=path)
    assert jobs[0]["tags"] == []
    assert jobs[0]["job_types"] == []
    Path(path).unlink(missing_ok=True)
    print("  PASS  test_empty_tags_and_job_types")


def test_remote_only_filter() -> None:
    path = _make_temp_db()
    upsert_jobs(_SAMPLE_JOBS, db_path=path)
    remote_jobs = get_jobs(db_path=path, remote_only=True)
    assert len(remote_jobs) == 1
    assert remote_jobs[0]["slug"] == "eng-acme-001"
    Path(path).unlink(missing_ok=True)
    print("  PASS  test_remote_only_filter")


def test_search_filter() -> None:
    path = _make_temp_db()
    upsert_jobs(_SAMPLE_JOBS, db_path=path)
    results = get_jobs(db_path=path, search="Designer")
    assert len(results) == 1
    assert results[0]["slug"] == "des-blob-002"
    Path(path).unlink(missing_ok=True)
    print("  PASS  test_search_filter")


def test_get_jobs_missing_db() -> None:
    jobs = get_jobs(db_path="/tmp/nonexistent_test_db_999.db")
    assert jobs == []
    print("  PASS  test_get_jobs_missing_db")


def test_count_jobs_missing_db() -> None:
    assert count_jobs(db_path="/tmp/nonexistent_test_db_999.db") == 0
    print("  PASS  test_count_jobs_missing_db")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Running storage tests...\n")

    tests = [
        test_init_db_creates_file,
        test_upsert_and_retrieve_single_job,
        test_upsert_multiple_jobs,
        test_upsert_no_duplicates_on_reingest,
        test_upsert_updates_on_conflict,
        test_empty_list_upsert,
        test_empty_tags_and_job_types,
        test_remote_only_filter,
        test_search_filter,
        test_get_jobs_missing_db,
        test_count_jobs_missing_db,
    ]

    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as exc:
            print(f"  FAIL  {test.__name__} – {exc}")
            failed += 1
        except Exception as exc:
            print(f"  ERROR {test.__name__} – {type(exc).__name__}: {exc}")
            failed += 1

    print(f"\n{len(tests) - failed}/{len(tests)} passed, {failed} failed")
    sys.exit(1 if failed else 0)
