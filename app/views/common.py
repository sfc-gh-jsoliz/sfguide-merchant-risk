"""Shared view helpers: load data with a skeleton, show Live errors (never fall back)."""
import time

import altair as alt
import streamlit as st

import brand
import data


def load(mode):
    ph = st.empty()
    if mode == "Live" and not st.session_state.get("_book_loaded"):
        ph.markdown(brand.skeleton(), unsafe_allow_html=True)
    try:
        df = data.book(mode)
        cf, src = data.cfpb(mode)
    except Exception as e:  # Live failure: show it, do not substitute sample data
        ph.empty()
        st.error(f"Live query failed: {e}")
        st.caption("Check that sql/setup.sql ran and your role is MERCHANT_RISK_ROLE, or switch to Sample.")
        st.stop()
    st.session_state["_book_loaded"] = True
    ph.empty()
    return df, cf, src


def cap(mode, text):
    return f"{'Live' if mode == 'Live' else 'Sample data'} · {text}"


def stream(text):
    for i, w in enumerate(text.split(" ")):
        yield w + " "
        if i % 3 == 0:
            time.sleep(0.012)


def theme():
    def _t():
        return {"config": {
            "font": "Instrument Sans",
            "view": {"stroke": None},
            "axis": {"labelColor": brand.T["muted"], "titleColor": brand.T["ink2"], "gridColor": brand.T["grid"],
                     "domainColor": brand.T["line"], "tickColor": brand.T["line"], "labelFontSize": 11,
                     "titleFontSize": 11, "titleFontWeight": 500},
            "axisX": {"grid": False},
            "legend": {"labelColor": brand.T["ink2"], "titleColor": brand.T["muted"], "labelFontSize": 11,
                       "titleFontSize": 11, "orient": "bottom", "symbolType": "square"},
            "background": "transparent",
        }}
    alt.themes.register("merchant_risk", _t)
    alt.themes.enable("merchant_risk")


def decision_scale():
    return alt.Scale(domain=data.DECISIONS, range=[brand.DEC_COLORS[d] for d in data.DECISIONS])
