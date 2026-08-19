"""
JobPulse — Job Listing Ingestion & Discovery

Acdyon Technologies Engineering Assessment
"""

from __future__ import annotations

import datetime
import html
import re
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


# ============================================================================
# PROJECT IMPORTS
# ============================================================================

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion import fetch_jobs
from src.storage import count_jobs, get_jobs, upsert_jobs


# ============================================================================
# SAFE DESCRIPTION RENDERING
# ============================================================================

def clean_job_description(value: object) -> str:
    """Convert API HTML descriptions into readable plain text safely.

    External job descriptions are not rendered as raw HTML. This avoids
    executing/rendering arbitrary markup while keeping the actual text
    readable in the UI.
    """
    if not value:
        return "No description available."

    text = str(value)

    # Turn common block/list tags into line breaks before stripping tags.
    text = re.sub(
        r"<\s*(br|/p|/li|/h[1-6]|/div|/ul|/ol)\s*/?>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    # Strip remaining HTML tags.
    text = re.sub(r"<[^>]+>", "", text)

    # Decode entities such as &amp;, &#x26;, etc.
    text = html.unescape(text)

    # Normalize whitespace while preserving paragraph/list line breaks.
    lines = []
    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)

    return "\n\n".join(lines)


# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="JobPulse",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================================
# THEME STATE + TOGGLE
# ============================================================================

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# The toggle must run BEFORE the theme colors and CSS are calculated.
# Streamlit reruns the script when the toggle changes, so the CSS is rebuilt
# immediately using the new theme values.
with st.sidebar:
    st.session_state.dark_mode = st.toggle(
        "Dark mode",
        value=st.session_state.dark_mode,
        key="theme_toggle",
    )

dark = st.session_state.dark_mode

if dark:
    BG = "#111827"
    SURFACE = "#172033"
    TEXT = "#f1f5f9"
    MUTED = "#94a3b8"
    BORDER = "#334155"
    INPUT = "#172033"
    BLUE = "#60a5fa"
    BLUE_HOVER = "#3b82f6"
    TAG_BG = "#1e293b"
else:
    BG = "#f8fafc"
    SURFACE = "#ffffff"
    TEXT = "#172033"
    MUTED = "#64748b"
    BORDER = "#e2e8f0"
    INPUT = "#ffffff"
    BLUE = "#2563eb"
    BLUE_HOVER = "#1d4ed8"
    TAG_BG = "#f8fafc"


# ============================================================================
# CSS
# ============================================================================

st.html(
    f"""
    <style>

    /* ================================================================
       GLOBAL
    ================================================================ */

    html,
    body,
    [data-testid="stApp"],
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .stApp {{
        background: {BG} !important;
        color: {TEXT} !important;
    }}

    [data-testid="stMainBlockContainer"] {{
        background: {BG} !important;
    }}

    [data-testid="stHeader"] {{
        background: transparent !important;
    }}

    .block-container {{
        max-width: 1120px;
        padding-top: 1.2rem;
        padding-bottom: 3rem;
    }}

    #MainMenu {{
        visibility: hidden;
    }}

    footer {{
        visibility: hidden;
    }}


    /* ================================================================
       STREAMLIT TEXT / CONTROLS
    ================================================================ */

    [data-testid="stWidgetLabel"] p {{
        color: {MUTED} !important;
    }}

    [data-testid="stTextInput"] input {{
        color: {TEXT} !important;
        background: {INPUT} !important;
    }}

    [data-testid="stSelectbox"] input {{
        color: {TEXT} !important;
    }}

    [data-testid="stCheckbox"] label,
    [data-testid="stCheckbox"] p {{
        color: {TEXT} !important;
    }}

    [data-baseweb="popover"],
    [data-baseweb="menu"] {{
        background: {SURFACE} !important;
    }}

    [role="option"] {{
        background: {SURFACE} !important;
        color: {TEXT} !important;
    }}

    [role="option"]:hover {{
        background: {TAG_BG} !important;
    }}

    /* ================================================================
       SIDEBAR
    ================================================================ */

    [data-testid="stSidebar"] {{
        background: {SURFACE} !important;
    }}

    [data-testid="stSidebar"] > div {{
        background: {SURFACE} !important;
    }}

    [data-testid="stSidebar"] * {{
        color: {TEXT};
    }}


    /* ================================================================
       NAVIGATION
    ================================================================ */

    .jp-nav {{
        display: flex;
        justify-content: space-between;
        align-items: center;

        padding: 8px 0 16px;

        border-bottom: 1px solid {BORDER};
    }}

    .jp-logo {{
        color: {TEXT};

        font-size: 21px;
        font-weight: 750;

        letter-spacing: -0.5px;
    }}

    .jp-logo-blue {{
        color: {BLUE};
    }}

    .jp-nav-right {{
        color: {MUTED};

        font-size: 13px;
    }}


    /* ================================================================
       HERO
    ================================================================ */

    .jp-home {{
        padding: 58px 0 34px;
        max-width: 820px;
    }}

    .jp-hero {{
        padding: 0;
        max-width: 820px;
    }}

    .jp-eyebrow {{
        color: {BLUE};

        font-size: 11px;
        font-weight: 750;

        letter-spacing: 1.7px;
        text-transform: uppercase;

        margin-bottom: 16px;
    }}

    .jp-hero-title {{
        color: {TEXT};

        font-size: 54px;
        line-height: 1.05;

        font-weight: 750;

        letter-spacing: -2.8px;

        margin-bottom: 18px;
    }}

    .jp-hero-blue {{
        color: {BLUE};
    }}

    .jp-hero-description {{
        color: {MUTED};

        font-size: 16px;
        line-height: 1.7;

        max-width: 680px;
    }}

    .jp-source {{
        color: {MUTED};

        font-size: 12px;

        margin-top: 15px;
    }}

    .jp-source a {{
        color: {BLUE};

        text-decoration: none;
    }}

    .jp-source a:hover {{
        text-decoration: underline;
    }}


    /* ================================================================
       EASTER EGG #1 (hidden keyboard-sequence reveal)
    ================================================================ */

    .jp-egg1-message {{
        display: none;

        color: {MUTED};

        font-size: 12px;
        line-height: 1.6;

        margin-top: 16px;

        opacity: 0.9;

        user-select: none;
    }}

    .jp-egg1-message.jp-egg1-visible {{
        display: block;
    }}


    /* ================================================================
       BUTTONS
    ================================================================ */

    .stButton > button {{
        background: {SURFACE} !important;

        color: {TEXT} !important;

        border: 1px solid {BORDER} !important;

        border-radius: 7px !important;

        font-weight: 650 !important;
    }}

    .stButton > button:hover {{
        border-color: {BLUE} !important;

        color: {BLUE} !important;
    }}

    button[kind="primary"] {{
        background: {BLUE} !important;

        color: #ffffff !important;

        border-color: {BLUE} !important;
    }}

    button[kind="primary"]:hover {{
        background: {BLUE_HOVER} !important;

        color: #ffffff !important;

        border-color: {BLUE_HOVER} !important;
    }}


    /* ================================================================
       STATISTICS
    ================================================================ */

    .jp-stats {{
        display: flex;
        width: 100%;
        border-top: 1px solid {BORDER};
        border-bottom: 1px solid {BORDER};
        margin: 22px 0 42px;
    }}

    .jp-stat {{
        flex: 1;

        padding: 20px 24px;

        border-right: 1px solid {BORDER};
    }}

    .jp-stat:first-child {{
        padding-left: 0;
    }}

    .jp-stat:last-child {{
        border-right: none;
    }}

    .jp-stat-value {{
        color: {TEXT};

        font-size: 28px;
        font-weight: 750;
    }}

    .jp-stat-label {{
        color: {MUTED};

        font-size: 10px;
        font-weight: 750;

        letter-spacing: 0.8px;

        margin-top: 4px;
    }}


    /* ================================================================
       SECTIONS
    ================================================================ */

    .jp-section-title {{
        color: {TEXT};

        font-size: 25px;
        font-weight: 720;

        letter-spacing: -0.6px;

        margin-bottom: 5px;
    }}

    .jp-section-description {{
        color: {MUTED};

        font-size: 14px;

        margin-bottom: 18px;
    }}


    /* ================================================================
       FILTER BOX
    ================================================================ */

    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {SURFACE} !important;

        border: 1px solid {BORDER} !important;

        border-radius: 9px !important;
    }}


    /* ================================================================
       TEXT INPUT
    ================================================================ */

    div[data-baseweb="input"] > div {{
        background: {INPUT} !important;

        border: 1px solid {BORDER} !important;

        border-radius: 7px !important;
    }}

    div[data-baseweb="input"] input {{
        background: {INPUT} !important;

        color: {TEXT} !important;
    }}

    div[data-baseweb="input"] input::placeholder {{
        color: {MUTED} !important;
    }}


    /* ================================================================
       SELECT
    ================================================================ */

    div[data-baseweb="select"] > div {{
        background: {INPUT} !important;

        border: 1px solid {BORDER} !important;

        border-radius: 7px !important;
    }}

    div[data-baseweb="select"] * {{
        color: {TEXT} !important;
    }}


    /* ================================================================
       CHECKBOX
    ================================================================ */

    div[data-testid="stCheckbox"] label {{
        color: {TEXT} !important;
    }}

    div[data-testid="stCheckbox"] p {{
        color: {TEXT} !important;
    }}


    /* ================================================================
       JOB LISTINGS
    ================================================================ */

    .jp-job {{
        padding: 24px 0;

        border-top: 1px solid {BORDER};
    }}

    .jp-job-title {{
        color: {TEXT};

        font-size: 19px;

        line-height: 1.4;

        font-weight: 700;
    }}

    .jp-company {{
        color: {MUTED};

        font-size: 14px;

        margin-top: 4px;
    }}

    .jp-meta {{
        color: {MUTED};

        font-size: 13px;

        margin-top: 8px;
    }}


    /* ================================================================
       REMOTE BADGE
    ================================================================ */

    .jp-remote {{
        display: inline-block;

        color: {BLUE};

        background: {"#172554" if dark else "#eff6ff"};

        border: 1px solid
            {"#1e3a8a" if dark else "#dbeafe"};

        border-radius: 20px;

        padding: 3px 8px;

        margin-left: 7px;

        font-size: 9px;

        font-weight: 750;

        letter-spacing: 0.5px;

        vertical-align: middle;
    }}


    /* ================================================================
       TAGS
    ================================================================ */

    .jp-tag {{
        display: inline-block;

        color: {MUTED};

        background: {TAG_BG};

        border: 1px solid {BORDER};

        border-radius: 5px;

        padding: 4px 8px;

        margin: 10px 5px 0 0;

        font-size: 11px;
    }}


    /* ================================================================
       EXPANDER
    ================================================================ */

    [data-testid="stExpander"] {{
        background: {SURFACE} !important;

        border: 1px solid {BORDER} !important;
    }}

    [data-testid="stExpander"] summary {{
        color: {TEXT} !important;
    }}


    /* ================================================================
       LINKS
    ================================================================ */

    .stMarkdown a {{
        color: {BLUE} !important;
    }}


    /* ================================================================
       CAPTIONS
    ================================================================ */

    [data-testid="stCaptionContainer"] {{
        color: {MUTED} !important;
    }}


    /* ================================================================
       MOBILE
    ================================================================ */

    @media (max-width: 700px) {{

        .jp-home {{
            padding-top: 42px;
        }}

        .jp-hero-title {{
            font-size: 40px;

            letter-spacing: -1.8px;
        }}

        .jp-hero-description {{
            font-size: 15px;
        }}

        .jp-stats {{
            display: block;
        }}

        .jp-stat {{
            border-right: none;

            border-bottom: 1px solid {BORDER};

            padding: 17px 0;
        }}

        .jp-stat:last-child {{
            border-bottom: none;
        }}

    }}

    </style>
    """
)


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:

    st.markdown(
        f"""
        <div style="
            color:{TEXT};
            font-size:21px;
            font-weight:750;
            margin-bottom:20px;
        ">
            Job<span style="color:{BLUE};">Pulse</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "A simple job discovery application built for the "
        "Acdyon Technologies Engineering Assessment."
    )

    st.divider()

    st.divider()

    st.markdown("**Data source**")
    st.caption("Arbeitnow Public Job Board API")

    st.markdown("**Storage**")
    st.caption("SQLite")

    st.markdown("**Ingestion**")
    st.caption("Pagination · pacing · retry/backoff")

    st.divider()

    st.caption(
        "Acdyon Technologies Engineering Assessment"
    )


# ============================================================================
# NAVIGATION
# ============================================================================
#
# EASTER EGG #2 (easy): hovering over the "JobPulse" wordmark reveals a
# small message. This is pure CSS (:hover) — no onclick handler, and the
# logo itself is not made clickable or interactive beyond the hover state.
# `user-select: none` keeps repeated clicks from selecting/highlighting the
# text.
# ============================================================================

st.html(
    f"""
    <style>
        .jp-secret-logo {{
            position: relative;
            cursor: default;
            user-select: none;
        }}

        .jp-secret-message {{
            position: absolute;
            left: 0;
            top: 31px;

            white-space: nowrap;

            color: {BLUE};
            font-size: 11px;
            font-weight: 500;

            opacity: 0;
            pointer-events: none;

            transition: opacity 0.2s ease;
        }}

        .jp-secret-logo:hover .jp-secret-message {{
            opacity: 1;
        }}
    </style>

    <div class="jp-nav">

        <div class="jp-logo jp-secret-logo">

            Job<span class="jp-logo-blue">Pulse</span>

            <span class="jp-secret-message">
                Nice catch. You found the other one. ✦
            </span>

        </div>

        <div class="jp-nav-right">
            Job Discovery · Public API
        </div>

    </div>
    """
)



# ============================================================================
# HERO / HOME PAGE
# ============================================================================

st.html(
    f"""
    <div class="jp-home">

        <div class="jp-eyebrow">
            JOB DISCOVERY
        </div>

        <div class="jp-hero-title">
            Find your next
            <span class="jp-hero-blue"> opportunity.</span>
        </div>

        <div class="jp-hero-description">
            Explore job listings collected from the Arbeitnow public API,
            normalized and stored locally for fast searching and filtering.
        </div>

        <div class="jp-source">
            Data provided by
            <a href="https://www.arbeitnow.com" target="_blank">
                Arbeitnow
            </a>
        </div>

        <div id="jp-egg1-message" class="jp-egg1-message">
            Ohh... I thought you'd never find it. 👀
        </div>

    </div>
    """
)


# ============================================================================
# EASTER EGG #1 (hard): hidden keyboard sequence
#
# ↑ ↑ ↓ ↓ ← → ← → B A
#
# Why this needs a component and not st.html/st.markdown:
# Streamlit's st.html / st.markdown(unsafe_allow_html=True) insert markup
# via innerHTML. Browsers never execute <script> tags that arrive through
# innerHTML assignment — so a <script> dropped into st.html looks like it
# should work but silently does nothing. That would be exactly the kind of
# "fake" implementation to avoid.
#
# st.components.v1.html renders its content inside a srcdoc iframe instead.
# A srcdoc iframe (without a sandbox attribute removing "allow-same-origin")
# inherits the embedding page's origin, so its script can genuinely reach
# `window.parent.document` and attach a real, working `keydown` listener on
# the actual app page — not just inside the isolated iframe.
#
# The listener:
#   - ignores keystrokes while an <input>/<textarea>/<select>/contenteditable
#     element is focused, so typing in the search box (or any widget) is
#     never touched
#   - never calls preventDefault(), so arrow-key navigation inside
#     selectboxes and normal scrolling keep working exactly as before
#   - never submits anything, changes filters, or reloads the page — it only
#     toggles a CSS class on a hidden, pre-existing message once the exact
#     sequence is completed
#   - remembers success in localStorage (scoped to the browser, not the
#     data layer) purely so the message stays revealed across Streamlit
#     reruns; it never touches SQLite, the ingestion pipeline, or any app
#     state
# ============================================================================

components.html(
    """
    <script>
    (function () {
        var sequence = [
            "ArrowUp", "ArrowUp",
            "ArrowDown", "ArrowDown",
            "ArrowLeft", "ArrowRight",
            "ArrowLeft", "ArrowRight",
            "b", "a"
        ];
        var progress = 0;

        var parentDoc, parentWin;
        try {
            parentDoc = window.parent.document;
            parentWin = window.parent;
        } catch (err) {
            parentDoc = document;
            parentWin = window;
        }

        function reveal() {
            try {
                var el = parentDoc.getElementById("jp-egg1-message");
                if (el) {
                    el.classList.add("jp-egg1-visible");
                }
                parentWin.localStorage.setItem("jp_egg1_found", "1");
            } catch (err) {
                /* no-op: keep the app running even if storage is blocked */
            }
        }

        function tryRevealFromPriorVisit(attemptsLeft) {
            var found = false;
            try {
                found = parentWin.localStorage.getItem("jp_egg1_found") === "1";
            } catch (err) {
                return;
            }
            if (!found) {
                return;
            }
            var el = parentDoc.getElementById("jp-egg1-message");
            if (el) {
                el.classList.add("jp-egg1-visible");
                return;
            }
            if (attemptsLeft > 0) {
                setTimeout(function () {
                    tryRevealFromPriorVisit(attemptsLeft - 1);
                }, 250);
            }
        }
        tryRevealFromPriorVisit(12);

        function isTypingTarget(target) {
            if (!target) {
                return false;
            }
            var tag = (target.tagName || "").toLowerCase();
            if (tag === "input" || tag === "textarea" || tag === "select") {
                return true;
            }
            if (target.isContentEditable) {
                return true;
            }
            return false;
        }

        function handleKeydown(e) {
            if (isTypingTarget(e.target)) {
                progress = 0;
                return;
            }

            var expected = sequence[progress];
            var key = e.key;
            var matches =
                key === expected ||
                (expected.length === 1 &&
                    typeof key === "string" &&
                    key.toLowerCase() === expected.toLowerCase());

            if (matches) {
                progress += 1;
                if (progress === sequence.length) {
                    reveal();
                    progress = 0;
                }
            } else {
                progress = key === sequence[0] ? 1 : 0;
            }
        }

        parentDoc.addEventListener("keydown", handleKeydown);
    })();
    </script>
    """,
    height=0,
)


# ============================================================================
# INGESTION
# ============================================================================

if st.button(
    "Fetch latest jobs",
    type="primary",
):

    with st.spinner("Fetching latest job listings..."):

        try:

            jobs = fetch_jobs()

            stored = upsert_jobs(jobs)

            st.success(
                f"Fetched {len(jobs)} jobs and stored {stored} records."
            )

        except Exception as exc:

            st.error(
                f"Ingestion failed: {type(exc).__name__}: {exc}"
            )


# ============================================================================
# STATISTICS
# ============================================================================

total = count_jobs()

if total > 0:

    all_jobs = get_jobs()

    remote_count = sum(
        1
        for job in all_jobs
        if job.get("remote")
    )

    location_count = len(
        {
            job.get("location")
            for job in all_jobs
            if job.get("location")
        }
    )

else:

    all_jobs = []

    remote_count = 0

    location_count = 0


st.html(
    f"""
    <div class="jp-stats">

        <div class="jp-stat">

            <div class="jp-stat-value">
                {total}
            </div>

            <div class="jp-stat-label">
                TOTAL JOBS
            </div>

        </div>

        <div class="jp-stat">

            <div class="jp-stat-value">
                {remote_count}
            </div>

            <div class="jp-stat-label">
                REMOTE JOBS
            </div>

        </div>

        <div class="jp-stat">

            <div class="jp-stat-value">
                {location_count}
            </div>

            <div class="jp-stat-label">
                LOCATIONS
            </div>

        </div>

    </div>
    """
)


# ============================================================================
# EMPTY DATABASE
# ============================================================================

if total == 0:

    st.html(
        """
        <div class="jp-section-title">
            Start exploring
        </div>

        <div class="jp-section-description">
            Fetch the latest listings to populate the job explorer.
        </div>
        """
    )

    st.info(
        "No jobs are stored yet. Click **Fetch latest jobs** above."
    )

    st.stop()


# ============================================================================
# EXPLORE
# ============================================================================

st.html(
    """
    <div class="jp-section-title">
        Explore opportunities
    </div>

    <div class="jp-section-description">
        Search and filter the available job listings.
    </div>
    """
)


# ============================================================================
# FILTERS
# ============================================================================

with st.container(border=True):

    col_search, col_location, col_remote = st.columns(
        [2.2, 1.4, 1.2]
    )

    with col_search:

        search_query = st.text_input(
            "Search",
            placeholder="Search jobs or companies...",
        )

    with col_location:

        locations = sorted(
            {
                job.get("location")
                for job in all_jobs
                if job.get("location")
            }
        )

        selected_location = st.selectbox(
            "Location",
            ["All locations"] + locations,
        )

    with col_remote:

        remote_only = st.checkbox(
            "Remote only"
        )


# ============================================================================
# FILTER DATA
# ============================================================================

# Keep the first page of results short so the home page stays compact.
# "Load more" reveals additional already-stored jobs without making another
# API request. A new search/filter starts again from the first page.
if "job_display_limit" not in st.session_state:
    st.session_state.job_display_limit = 12

filter_signature = (
    search_query.strip(),
    selected_location,
    remote_only,
)

if st.session_state.get("job_filter_signature") != filter_signature:
    st.session_state.job_filter_signature = filter_signature
    st.session_state.job_display_limit = 12

filtered = get_jobs(
    search=search_query or None,
    remote_only=remote_only,
)

if selected_location != "All locations":

    filtered = [
        job
        for job in filtered
        if job.get("location") == selected_location
    ]


if not filtered:

    st.warning(
        "No jobs match your current filters. "
        "Try a different search or location."
    )

    st.stop()

visible_jobs = filtered[:st.session_state.job_display_limit]

st.caption(
    f"Showing {len(visible_jobs)} of {len(filtered)} matching jobs"
)


# ============================================================================
# JOB LIST
# ============================================================================

for job in visible_jobs:

    title = str(
        job.get("title") or "Untitled"
    )

    company = str(
        job.get("company_name") or "Unknown"
    )

    location = str(
        job.get("location") or ""
    )

    job_types = job.get("job_types") or []

    tags = job.get("tags") or []

    url = str(
        job.get("url") or ""
    )


    # ------------------------------------------------------------------------
    # DATE
    # ------------------------------------------------------------------------

    created = ""

    if job.get("created_at"):

        try:

            dt = datetime.datetime.fromtimestamp(
                job["created_at"],
                tz=datetime.timezone.utc,
            )

            created = dt.strftime(
                "%d %b %Y"
            )

        except (
            OSError,
            ValueError,
            TypeError,
        ):

            created = ""


    # ------------------------------------------------------------------------
    # META
    # ------------------------------------------------------------------------

    meta_parts = []

    if location:
        meta_parts.append(location)

    if job_types:

        meta_parts.append(
            ", ".join(
                str(item)
                for item in job_types
            )
        )

    if created:
        meta_parts.append(created)

    meta_text = " · ".join(meta_parts)


    # ------------------------------------------------------------------------
    # REMOTE BADGE
    # ------------------------------------------------------------------------

    remote_html = ""

    if job.get("remote"):

        remote_html = (
            '<span class="jp-remote">'
            'REMOTE'
            '</span>'
        )


    # ------------------------------------------------------------------------
    # TAGS
    # ------------------------------------------------------------------------

    tags_html = ""

    for tag in tags:

        safe_tag = html.escape(
            str(tag)
        )

        tags_html += (
            '<span class="jp-tag">'
            f'{safe_tag}'
            '</span>'
        )


    # ------------------------------------------------------------------------
    # ESCAPE VALUES
    # ------------------------------------------------------------------------

    safe_title = html.escape(title)

    safe_company = html.escape(company)

    safe_meta = html.escape(meta_text)


    # ------------------------------------------------------------------------
    # JOB HEADER
    # ------------------------------------------------------------------------

    st.html(
        f"""
        <div class="jp-job">

            <div class="jp-job-title">
                {safe_title}
                {remote_html}
            </div>

            <div class="jp-company">
                {safe_company}
            </div>

            <div class="jp-meta">
                {safe_meta}
            </div>

            <div>
                {tags_html}
            </div>

        </div>
        """
    )


    # ------------------------------------------------------------------------
    # ORIGINAL LISTING
    # ------------------------------------------------------------------------

    if url:

        safe_url = html.escape(
            url,
            quote=True,
        )

        st.markdown(
            f"[View original listing →]({safe_url})"
        )


    # ------------------------------------------------------------------------
    # DESCRIPTION
    # ------------------------------------------------------------------------

    with st.expander(
        f"View description — {title}"
    ):

        description = clean_job_description(job.get("description"))

        # External HTML is converted to safe readable text first.
        st.markdown(description)


# ============================================================================
# LOAD MORE
# ============================================================================

remaining_jobs = len(filtered) - len(visible_jobs)

if remaining_jobs > 0:
    load_count = min(12, remaining_jobs)

    if st.button(
        f"Load more jobs ({remaining_jobs} remaining)",
        key="load_more_jobs",
        use_container_width=True,
    ):
        st.session_state.job_display_limit += load_count
        st.rerun()
else:
    st.caption("You've reached the end of the current results.")


# ============================================================================
# FOOTER
# ============================================================================

st.html(
    f"""
    <div class="jp-footer">

        JobPulse · Acdyon Technologies Engineering Assessment
        · Data from the
        <a
            href="https://www.arbeitnow.com"
            target="_blank"
            style="
                color:{BLUE};
                text-decoration:none;
            "
        >
            Arbeitnow
        </a>
        Public Job Board API

    </div>
    """
)