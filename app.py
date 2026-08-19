"""
JobPulse
Job Listing Ingestion Dashboard

Acdyon Technologies Engineering Assessment.

Backend:
    src.ingestion.fetch_jobs
    src.storage.get_jobs
    src.storage.upsert_jobs
    src.storage.count_jobs

Frontend:
    Streamlit native components + small CSS theme layer.
"""

from __future__ import annotations

import datetime
import html
import re
import sys
from pathlib import Path

import streamlit as st


# ============================================================
# PROJECT SETUP
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion import fetch_jobs
from src.storage import count_jobs, get_jobs, upsert_jobs


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="JobPulse",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# SESSION STATE
# ============================================================

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

if "display_limit" not in st.session_state:
    st.session_state.display_limit = 12

if "last_filter" not in st.session_state:
    st.session_state.last_filter = None

if "star_clicks" not in st.session_state:
    st.session_state.star_clicks = 0

if "logo_clicks" not in st.session_state:
    st.session_state.logo_clicks = 0


# ============================================================
# THEME
# ============================================================

dark = st.session_state.dark_mode

if dark:
    BG = "#0f172a"
    SURFACE = "#111827"
    TEXT = "#f8fafc"
    MUTED = "#94a3b8"
    BORDER = "#334155"
    BLUE = "#60a5fa"
    INPUT = "#111827"
    HOVER = "#172033"
else:
    BG = "#f8fafc"
    SURFACE = "#ffffff"
    TEXT = "#172033"
    MUTED = "#64748b"
    BORDER = "#dbe3ef"
    BLUE = "#2563eb"
    INPUT = "#ffffff"
    HOVER = "#eff6ff"


# ============================================================
# CSS
# ============================================================
#
# IMPORTANT:
# This CSS does NOT contain page content.
# All actual page content below uses native Streamlit widgets.
# ============================================================

st.markdown(
    f"""
<style>
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"] {{
    background: {BG} !important;
    color: {TEXT} !important;
}}

.block-container {{
    max-width: 1080px;
    padding-top: 1.2rem;
    padding-bottom: 4rem;
}}

[data-testid="stHeader"] {{
    background: transparent !important;
}}

[data-testid="stSidebar"],
[data-testid="stSidebar"] > div {{
    background: {SURFACE} !important;
}}

[data-testid="stTextInput"] input {{
    background: {INPUT} !important;
    color: {TEXT} !important;
}}

[data-baseweb="select"] > div,
[data-baseweb="input"] > div {{
    background: {INPUT} !important;
    border-color: {BORDER} !important;
}}

[data-baseweb="popover"],
[data-baseweb="menu"],
[role="option"] {{
    background: {SURFACE} !important;
    color: {TEXT} !important;
}}

[role="option"]:hover {{
    background: {HOVER} !important;
}}

[data-testid="stWidgetLabel"] p,
[data-testid="stCheckbox"] label,
[data-testid="stCheckbox"] p {{
    color: {MUTED} !important;
}}

.stButton > button {{
    background: {SURFACE} !important;
    color: {TEXT} !important;
    border: 1px solid {BORDER} !important;
    border-radius: 6px !important;
    font-weight: 650 !important;
}}

.stButton > button:hover {{
    color: {BLUE} !important;
    border-color: {BLUE} !important;
}}

button[kind="primary"] {{
    background: {BLUE} !important;
    color: #ffffff !important;
    border-color: {BLUE} !important;
}}

button[kind="primary"]:hover {{
    background: {BLUE} !important;
    color: #ffffff !important;
}}

[data-testid="stExpander"] {{
    background: {SURFACE} !important;
    border-color: {BORDER} !important;
}}

[data-testid="stExpander"] details,
[data-testid="stExpander"] summary {{
    background: {SURFACE} !important;
    color: {TEXT} !important;
}}

.jp-title {{
    font-size: clamp(40px, 5.5vw, 62px);
    line-height: 1.04;
    letter-spacing: -3px;
    font-weight: 800;
    color: {TEXT};
}}

.jp-eyebrow {{
    color: {BLUE};
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1.8px;
    text-transform: uppercase;
}}

.jp-description {{
    color: {MUTED};
    font-size: 16px;
    line-height: 1.7;
    max-width: 700px;
}}

.jp-source {{
    color: {MUTED};
    font-size: 12px;
}}

.jp-source a {{
    color: {BLUE};
    text-decoration: none;
}}

.jp-job-title {{
    font-size: 18px;
    font-weight: 800;
    color: {TEXT};
}}

.jp-company {{
    font-size: 13px;
    font-weight: 650;
    color: {BLUE};
}}

.jp-meta {{
    font-size: 12px;
    color: {MUTED};
}}

.jp-tag {{
    font-size: 10px;
    color: {MUTED};
    border: 1px solid {BORDER};
    border-radius: 4px;
    padding: 4px 7px;
}}

.jp-remote {{
    font-size: 9px;
    font-weight: 800;
    color: {BLUE};
    background: {HOVER};
    border-radius: 4px;
    padding: 3px 7px;
}}

@media (max-width: 700px) {{
    .block-container {{
        padding-left: 1rem;
        padding-right: 1rem;
    }}

    .jp-title {{
        font-size: 42px;
        letter-spacing: -2px;
    }}

    .jp-description {{
        font-size: 14px;
    }}
}}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.title("JobPulse")
    st.caption(
        "Job discovery dashboard for the Acdyon Technologies "
        "Engineering Assessment."
    )

    st.divider()

    st.markdown("**Data source**")
    st.write("Arbeitnow Public Job Board API")

    st.markdown("**Storage**")
    st.write("SQLite")

    st.markdown("**Ingestion**")
    st.write("Rate-limited · paginated · retry/backoff")


# ============================================================
# NAVIGATION
# ============================================================

nav_left, nav_right = st.columns([5, 1])

with nav_left:
    st.subheader("JobPulse")

with nav_right:
    st.caption("Job discovery")

st.divider()

# ============================================================
# DARK MODE
# ============================================================

theme_left, theme_center, theme_right = st.columns([4, 2, 4])

with theme_center:
    new_dark_mode = st.toggle(
        "Dark mode",
        value=st.session_state.dark_mode,
        key="theme_toggle",
    )

if new_dark_mode != st.session_state.dark_mode:
    st.session_state.dark_mode = new_dark_mode
    st.rerun()


# ============================================================
# HERO
# ============================================================

st.markdown(
    '<div class="jp-eyebrow">JOB DISCOVERY</div>',
    unsafe_allow_html=True,
)

st.title("Find your next opportunity.")

st.markdown(
    "Explore job listings collected from the **Arbeitnow public API**, "
    "normalized and stored locally for fast searching and filtering."
)

st.caption("Data provided by Arbeitnow")


# ============================================================
# FETCH
# ============================================================

fetch_col, _ = st.columns([1.6, 5])

with fetch_col:
    fetch_clicked = st.button(
        "Fetch Latest Jobs",
        type="primary",
        use_container_width=True,
    )

if fetch_clicked:
    with st.spinner("Fetching latest jobs..."):
        try:
            jobs = fetch_jobs()
            stored = upsert_jobs(jobs)

            st.session_state.display_limit = 12

            st.success(
                f"Fetched {len(jobs)} jobs and stored {stored} records."
            )

            st.rerun()

        except Exception as exc:
            st.error(
                f"Ingestion failed: {type(exc).__name__}: {exc}"
            )


# ============================================================
# DATABASE
# ============================================================

total = count_jobs()
all_jobs = get_jobs()

remote_count = sum(
    1 for job in all_jobs if job.get("remote")
)

location_count = len(
    {
        str(job.get("location"))
        for job in all_jobs
        if job.get("location")
    }
)


# ============================================================
# STATS
# ============================================================

stat1, stat2, stat3 = st.columns(3)

with stat1:
    st.metric("Jobs", total)

with stat2:
    st.metric("Remote", remote_count)

with stat3:
    st.metric("Locations", location_count)


st.divider()


# ============================================================
# SEARCH
# ============================================================

st.subheader("Explore Opportunities")
st.caption("Search and filter the available job listings.")

search_col, location_col, remote_col = st.columns([3, 1.8, 1])

with search_col:
    search_query = st.text_input(
        "Search",
        placeholder="Search jobs or companies...",
    )

with location_col:
    locations = sorted(
        {
            str(job.get("location"))
            for job in all_jobs
            if job.get("location")
        }
    )

    selected_location = st.selectbox(
        "Location",
        ["All locations"] + locations,
    )

with remote_col:
    remote_only = st.checkbox("Remote only")


# ============================================================
# FILTER
# ============================================================

filtered = get_jobs(
    search=search_query.strip() or None,
    remote_only=remote_only,
)

if selected_location != "All locations":
    filtered = [
        job
        for job in filtered
        if job.get("location") == selected_location
    ]


current_filter = (
    search_query.strip().lower(),
    selected_location,
    remote_only,
)

if st.session_state.last_filter is None:
    st.session_state.last_filter = current_filter

elif current_filter != st.session_state.last_filter:
    st.session_state.last_filter = current_filter
    st.session_state.display_limit = 12


# ============================================================
# DESCRIPTION CLEANER
# ============================================================

def clean_job_description(value: object) -> str:
    """Convert API HTML description to readable text."""

    if not value:
        return "No description available."

    text = html.unescape(str(value))

    text = re.sub(
        r"<\s*(br|/p|/li|/h[1-6]|/div|/ul|/ol)\s*/?>",
        "\n",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"<[^>]+>",
        "",
        text,
    )

    text = html.unescape(text)

    lines = []

    for line in text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()

        if line:
            lines.append(line)

    return "\n\n".join(lines) or "No description available."


# ============================================================
# JOB RESULTS
# ============================================================

if not filtered:
    st.info("No jobs match your current filters.")

else:
    visible_count = min(
        st.session_state.display_limit,
        len(filtered),
    )

    st.caption(
        f"Showing {visible_count} of {len(filtered)} matching jobs"
    )

    for index, job in enumerate(filtered[:visible_count]):

        title = job.get("title") or "Untitled position"
        company = job.get("company_name") or "Unknown company"
        location = job.get("location") or "Location not specified"

        job_types = job.get("job_types") or []
        tags = job.get("tags") or []

        created = ""

        if job.get("created_at"):
            try:
                created = datetime.datetime.fromtimestamp(
                    job["created_at"],
                    tz=datetime.timezone.utc,
                ).strftime("%d %b %Y")
            except (OSError, ValueError, TypeError):
                created = ""

        # Native Streamlit job presentation.
        st.markdown(f"### {title}")
        st.markdown(f"**{company}**")

        meta = [str(location)]

        if job_types:
            meta.append(
                ", ".join(str(x) for x in job_types)
            )

        if created:
            meta.append(created)

        st.caption(" · ".join(meta))

        if job.get("remote"):
            st.info("🌐 Remote")

        if tags:
            st.write(
                " ".join(
                    f"`{tag}`"
                    for tag in tags[:8]
                )
            )

        url = job.get("url")

        if url:
            st.markdown(
                f"[View original listing →]({url})"
            )

        with st.expander(
            f"View description — {title}"
        ):
            st.write(
                clean_job_description(
                    job.get("description")
                )
            )

        if index < visible_count - 1:
            st.divider()


# ============================================================
# LOAD MORE
# ============================================================

remaining = len(filtered) - min(
    st.session_state.display_limit,
    len(filtered),
)

if remaining > 0:
    load_left, load_center, load_right = st.columns(
        [2, 2, 2]
    )

    with load_center:
        if st.button(
            f"Load More · {remaining} remaining",
            use_container_width=True,
            key="load_more_jobs",
        ):
            st.session_state.display_limit += 12
            st.rerun()

elif filtered:
    st.caption("You've reached the end of the current results.")


# ============================================================
# HIDDEN EASTER EGGS
# ============================================================
#
# IMPORTANT:
# There are NO visible Easter-egg buttons.
#
# Egg 1:
# A Konami-style keyboard sequence:
#   ↑ ↑ ↓ ↓ ← → ← →
#
# Egg 2:
# Hold the small "Job discovery" navbar text for 2 seconds.
#
# Neither trigger has a visible rectangle, icon, tooltip, or label.
# Both open the same centered Streamlit dialog.
# ============================================================

@st.dialog("You found it")
def show_easter_egg():
    st.markdown("## Ohh... I thought you'd never find it. 👀")

    st.write("You made it all the way down here.")

    st.write(
        "I hope this little detail made you smile."
    )

    st.write(
        "And maybe, if things work out, "
        "I hope we get a chance to work together. ✦"
    )


# ------------------------------------------------------------
# Invisible native trigger
# ------------------------------------------------------------
#
# The button exists only so a browser-side event can ask Streamlit
# to rerun. CSS removes it completely from the visual layout.
# ------------------------------------------------------------

st.markdown(
    """
<style>
button.jp-hidden-trigger,
.jp-hidden-trigger-wrap {
    display: none !important;
}
</style>

<script>
(function () {
    if (window.__jpEggsInstalled) return;
    window.__jpEggsInstalled = true;

    let sequence = [];
    let holdTimer = null;

    const konami = [
        "ArrowUp",
        "ArrowUp",
        "ArrowDown",
        "ArrowDown",
        "ArrowLeft",
        "ArrowRight",
        "ArrowLeft",
        "ArrowRight"
    ];

    function findHiddenButton() {
        const buttons = Array.from(
            document.querySelectorAll("button")
        );

        return buttons.find(function (button) {
            return button.getAttribute("aria-label")
                === "jobpulse-hidden-egg";
        });
    }

    function triggerEgg() {
        const button = findHiddenButton();

        if (button) {
            button.click();
        }
    }

    document.addEventListener("keydown", function (event) {
        sequence.push(event.key);

        if (sequence.length > konami.length) {
            sequence.shift();
        }

        if (
            sequence.length === konami.length &&
            sequence.every(
                function (key, index) {
                    return key === konami[index];
                }
            )
        ) {
            sequence = [];
            triggerEgg();
        }
    });

    function installHoldTarget() {
        const candidates = Array.from(
            document.querySelectorAll("p, span, div")
        );

        const target = candidates.find(function (element) {
            return (
                element.offsetParent !== null &&
                element.textContent.trim() === "Job discovery"
            );
        });

        if (!target || target.dataset.jpEggHold === "1") {
            return;
        }

        target.dataset.jpEggHold = "1";

        target.addEventListener("pointerdown", function () {
            clearTimeout(holdTimer);

            holdTimer = setTimeout(function () {
                triggerEgg();
            }, 2000);
        });

        ["pointerup", "pointerleave", "pointercancel"].forEach(
            function (eventName) {
                target.addEventListener(
                    eventName,
                    function () {
                        clearTimeout(holdTimer);
                        holdTimer = null;
                    }
                );
            }
        );
    }

    installHoldTarget();
    setInterval(installHoldTarget, 1000);
})();
</script>
""",
    unsafe_allow_html=True,
)

# This is deliberately blank and is completely hidden by CSS after
# Streamlit renders it. The browser script gives it an aria-label so
# it can find it without exposing anything to the user.
st.markdown(
    """
<script>
(function () {
    function hideEggButton() {
        const buttons = Array.from(
            document.querySelectorAll("button")
        );

        const blank = buttons.find(function (button) {
            return (
                button.innerText.trim() === "" &&
                !button.getAttribute("aria-label")
            );
        });

        if (blank) {
            blank.setAttribute(
                "aria-label",
                "jobpulse-hidden-egg"
            );

            blank.style.display = "none";
        }
    }

    hideEggButton();
    setTimeout(hideEggButton, 300);
    setTimeout(hideEggButton, 900);
    setTimeout(hideEggButton, 1600);
})();
</script>
""",
    unsafe_allow_html=True,
)

if st.button(
    "",
    key="jobpulse_hidden_egg",
):
    show_easter_egg()

# ============================================================
# FINAL FOOTER
# ============================================================

st.caption(
    "JobPulse · Acdyon Technologies Engineering Assessment"
)

st.caption(
    "Data from the Arbeitnow Public Job Board API."
)