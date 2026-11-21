"""Merchant Risk & Underwriting on Snowflake.

Run locally (Sample mode, no account):   streamlit run app/streamlit_app.py
Live mode locally: set SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER and SNOWFLAKE_PRIVATE_KEY_PATH
(key-pair auth) and restart. In Streamlit in Snowflake the app uses its own session.
"""
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import brand  # noqa: E402
import data  # noqa: E402
from views import applications, ask, notes, portfolio, segments  # noqa: E402

st.set_page_config(page_title="Merchant Risk & Underwriting", page_icon="⚖️", layout="wide",
                   initial_sidebar_state="auto")
st.markdown(brand.CSS, unsafe_allow_html=True)

LIVE_OK = data.live_configured()
if "mode" not in st.session_state:
    st.session_state.mode = "Live" if LIVE_OK else "Sample"

VIEWS = {
    "Portfolio": portfolio.render,
    "Applications": applications.render,
    "Segments": segments.render,
    "Underwriting notes": notes.render,
    "Ask the agent": ask.render,
}

with st.sidebar:
    st.html(f'<div class="mr-brand">{brand.LOGO_IMG}<div><b>Merchant Risk &amp; Underwriting</b>'
            '<span>New-merchant scoring · acquirer underwriting desk</span></div></div>')
    st.html('<p class="mr-label">Data mode</p>')
    st.segmented_control("Data mode", ["Sample", "Live"], key="mode", label_visibility="collapsed",
                         help="Sample: bundled synthetic data, no account. Live: the same app on Snowflake.")
    mode = st.session_state.mode or st.session_state.get("_last_mode", "Sample")
    st.session_state["_last_mode"] = mode
    st.html(f'<div style="display:flex;gap:.4rem;flex-wrap:wrap;margin-top:.5rem">{brand.env_chip(mode)}'
            f'<span class="mr-chip role">Underwriter · {data.ROLE}</span></div>')
    st.html('<p class="mr-label">Workspace</p>')
    with st.container(key="nav"):
        view = st.radio("View", list(VIEWS), label_visibility="collapsed", key="view")
    st.html('<p class="mr-side-foot">Synthetic data and illustrative scoring only. Not a production underwriting '
            'system or credit advice.</p>')

if mode == "Live" and not LIVE_OK:
    st.markdown(brand.header("Connect Live mode", "Live mode runs this same app on Snowflake. No connection is configured, "
                             "so nothing is shown instead of falling back to sample data.", "Setup needed", "Live"),
                unsafe_allow_html=True)
    st.markdown("1. Run `sql/setup.sql` in a Snowsight worksheet (about 15 s on an XSMALL warehouse).\n"
                "2. Register a key pair on your Snowflake user, then set these variables and restart:")
    st.code("export SNOWFLAKE_ACCOUNT=<org-account>\nexport SNOWFLAKE_USER=<YOUR_USER>\n"
            "export SNOWFLAKE_PRIVATE_KEY_PATH=~/.snowflake/keys/<your_key>.p8\n"
            "streamlit run app/streamlit_app.py", language="bash")
    st.markdown("Or deploy the app as Streamlit in Snowflake (README, *Deploy the app in Snowflake*). "
                "Switch back to **Sample** to keep exploring.")
    st.stop()

VIEWS[view](mode)
