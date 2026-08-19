"""
Smoke test for src/ingestion.py

Makes a single API call (max_pages=1) and verifies the basic structure.
No mocking — hits the real API once.
"""

import sys
from pathlib import Path

# Ensure the project root is on sys.path so src.ingestion is importable.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion import KNOWN_FIELDS, fetch_jobs


def test_fetch_one_page() -> None:
    """Fetch page 1 only and validate the result."""
    jobs = fetch_jobs(max_pages=1)

    # 1. Must return a list.
    assert isinstance(jobs, list), f"Expected list, got {type(jobs).__name__}"

    # 2. Must contain at least one job.
    assert len(jobs) > 0, "Expected at least 1 job, got 0"

    # 3. Each job must have all expected normalised keys.
    for i, job in enumerate(jobs):
        for field in KNOWN_FIELDS:
            assert field in job, f"Job #{i} missing field '{field}'"


if __name__ == "__main__":
    print("Running smoke test (fetching page 1)...\n")
    try:
        test_fetch_one_page()
        print("PASS – all assertions succeeded.")
    except AssertionError as exc:
        print(f"FAIL – {exc}")
        sys.exit(1)
    except Exception as exc:
        print(f"ERROR – {type(exc).__name__}: {exc}")
        sys.exit(1)
