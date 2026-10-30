import streamlit as st


STYLE = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');

:root {
    --paper: #f6f4ee;
    --surface: #fffdfa;
    --ink: #202b2e;
    --muted: #6b7777;
    --line: #dedfd8;
    --teal: #176b63;
    --teal-dark: #0e4b47;
    --coral: #d66b4d;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: var(--ink);
}

.stApp {
    background: var(--paper);
}

[data-testid="stHeader"] {
    background: transparent;
}

[data-testid="stSidebar"] {
    background: var(--teal-dark);
    border-right: 0;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {
    color: #eaf3ef;
}

[data-testid="stSidebar"] .stMarkdown p {
    color: #b7cfca;
}

[data-testid="stSidebar"] a {
    color: #eef7f3;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.16);
}

.block-container {
    max-width: 1440px;
    padding: 3.25rem 4rem 4rem;
}

h1, h2, h3 {
    font-family: 'Space Grotesk', sans-serif;
    color: var(--ink);
    letter-spacing: 0;
}

h1 {
    font-size: 2.45rem;
    line-height: 1.05;
    margin-bottom: 0.45rem;
}

h2 {
    font-size: 1.45rem;
}

h3 {
    font-size: 1.05rem;
}

.page-kicker {
    color: var(--coral);
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}

.page-subtitle {
    color: var(--muted);
    font-size: 1rem;
    margin-bottom: 2rem;
}

[data-testid="stMetric"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 1.05rem 1.15rem;
    box-shadow: 0 8px 24px rgba(32, 43, 46, 0.04);
}

[data-testid="stMetricLabel"] {
    color: var(--muted);
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

[data-testid="stMetricValue"] {
    color: var(--teal-dark);
    font-family: 'Space Grotesk', sans-serif;
}

[data-testid="stForm"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 1.25rem 1.35rem 1rem;
    box-shadow: 0 8px 24px rgba(32, 43, 46, 0.035);
}

[data-baseweb="tab-list"] {
    gap: 1.6rem;
    border-bottom: 1px solid var(--line);
}

button[data-baseweb="tab"] {
    color: var(--muted);
    font-weight: 600;
    padding: 0.8rem 0.15rem;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--teal);
}

button[kind="primary"], button[data-testid="baseButton-primaryFormSubmit"] {
    background: var(--coral);
    border-color: var(--coral);
    color: white;
    font-weight: 700;
}

button[kind="primary"]:hover, button[data-testid="baseButton-primaryFormSubmit"]:hover {
    background: #bb583d;
    border-color: #bb583d;
}

input, textarea, [data-baseweb="select"] > div {
    border-color: var(--line) !important;
    background: #fcfbf7 !important;
}

[data-testid="stDataFrame"] {
    border: 1px solid var(--line);
    border-radius: 8px;
    overflow: hidden;
    background: var(--surface);
}

[data-testid="stAlert"] {
    border-radius: 8px;
}

[data-testid="stPlotlyChart"] {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: 8px;
    padding: 0.35rem;
}

[data-testid="stSidebarNav"] {
    padding-top: 1rem;
}

[data-testid="stSidebarNav"] li a {
    border-radius: 6px;
    margin: 0.15rem 0.7rem;
}

[data-testid="stSidebarNav"] li a:hover {
    background: rgba(255, 255, 255, 0.11);
}

@media (max-width: 900px) {
    .block-container {
        padding: 2rem 1.1rem 3rem;
    }

    h1 {
        font-size: 2rem;
    }
}
</style>
"""


def apply_styles() -> None:
    st.markdown(STYLE, unsafe_allow_html=True)
    st.sidebar.markdown(
        "<div style='font-family: Space Grotesk, sans-serif; font-size: 1.15rem; "
        "font-weight: 700; color: #f4faf7; padding: 0.5rem 0 1.5rem;'>People Ops<br>Analytics</div>",
        unsafe_allow_html=True,
    )


def page_header(kicker: str, title: str, subtitle: str) -> None:
    st.markdown(f"<div class='page-kicker'>{kicker}</div>", unsafe_allow_html=True)
    st.title(title)
    st.markdown(f"<div class='page-subtitle'>{subtitle}</div>", unsafe_allow_html=True)
