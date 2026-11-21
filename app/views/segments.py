"""Segments: category x credit tier matrix, score distribution and period change."""
import altair as alt
import pandas as pd
import streamlit as st

import brand
import data
from views.common import cap, decision_scale, load, theme

METRICS = {"Decline rate": ("decline_rate", ".1%", "#B02A1E"), "Approval rate": ("approval_rate", ".1%", "#1D6B47"),
           "Average risk score": ("avg_score", ".1f", "#7D2A3C"), "Avg reserve, booked (%)": ("avg_reserve_booked", ".2f", "#36587A")}


def render(mode):
    theme()
    df, _, _ = load(mode)
    st.markdown(brand.header(
        "Segments", "Where risk concentrates: merchant category against applicant credit tier, the full score distribution, "
        "and how each category moved between the first and last six months.", cap(mode, "MERCHANT_RISK_BOOK view"), mode),
        unsafe_allow_html=True)

    seg = data.segments(df)
    with st.container(key="card_heat"):
        c1, c2 = st.columns([3, 1.4], vertical_alignment="bottom")
        c1.markdown('<p class="mr-card-h">Category × credit tier</p><p class="mr-card-s">About 30 applications per cell. '
                    'Hover a cell for the full figures.</p>', unsafe_allow_html=True)
        metric = c2.selectbox("Metric", list(METRICS), key="seg_metric", label_visibility="collapsed")
        col, fmt, color = METRICS[metric]
        heat = alt.Chart(seg).mark_rect(cornerRadius=3, stroke="#fff", strokeWidth=2).encode(
            x=alt.X("tier:N", title=None, sort=data.TIERS, axis=alt.Axis(labelAngle=0, orient="top")),
            y=alt.Y("category:N", title=None, sort=sorted(seg.category.unique())),
            color=alt.Color(f"{col}:Q", title=metric, scale=alt.Scale(range=["#F7F4F0", color]),
                            legend=alt.Legend(orient="bottom", format=fmt, gradientLength=220)),
            tooltip=[alt.Tooltip("category:N", title="Category"), alt.Tooltip("tier:N", title="Credit tier"),
                     alt.Tooltip("applications:Q", title="Applications"),
                     alt.Tooltip("approval_rate:Q", title="Approval rate", format=".1%"),
                     alt.Tooltip("decline_rate:Q", title="Decline rate", format=".1%"),
                     alt.Tooltip("avg_score:Q", title="Avg risk score", format=".1f"),
                     alt.Tooltip("avg_reserve_booked:Q", title="Avg reserve, booked %", format=".2f")])
        text = alt.Chart(seg).mark_text(font="Red Hat Mono", fontSize=12, fontWeight=600).encode(
            x=alt.X("tier:N", sort=data.TIERS), y=alt.Y("category:N", sort=sorted(seg.category.unique())),
            text=alt.Text(f"{col}:Q", format=fmt),
            color=alt.condition(f"datum.{col} > {seg[col].quantile(.6)}", alt.value("#FFFFFF"), alt.value("#1E1A1B")))
        st.altair_chart((heat + text).properties(height=300), width="stretch", theme=None)

    left, right = st.columns([1.3, 1], gap="medium")
    with left.container(key="card_hist"):
        st.markdown('<p class="mr-card-h">Risk score distribution</p><p class="mr-card-s">5-point bins, coloured by the decision '
                    'each score produced. Thresholds at 40 and 70.</p>', unsafe_allow_html=True)
        h = df.assign(bin=(df.risk_score // 5 * 5).clip(upper=95))
        h = h.groupby(["bin", "decision"]).size().reset_index(name="count")
        h["bin_end"] = h["bin"] + 5
        bars = alt.Chart(h).mark_bar(stroke="#fff", strokeWidth=1).encode(
            x=alt.X("bin:Q", title="Risk score", scale=alt.Scale(domain=[0, 100])), x2="bin_end:Q",
            y=alt.Y("count:Q", title="Applications", stack="zero"),
            color=alt.Color("decision:N", title=None, scale=decision_scale()),
            tooltip=[alt.Tooltip("bin:Q", title="Score from"), alt.Tooltip("decision:N", title="Decision"),
                     alt.Tooltip("count:Q", title="Applications")])
        rules = alt.Chart(pd.DataFrame({"x": [40, 70]})).mark_rule(color="#1E1A1B", strokeDash=[4, 3]).encode(x="x:Q")
        st.altair_chart((bars + rules).properties(height=260), width="stretch", theme=None)
    with right.container(key="card_shift"):
        st.markdown('<p class="mr-card-h">Decline rate: first vs last six months</p><p class="mr-card-s">'
                    'Jul-Dec 2024 against Jan-Jun 2026, by category.</p>', unsafe_allow_html=True)
        p = df[(df.month <= "2024-12-31") | (df.month >= "2026-01-01")].copy()
        p["period"] = p.month.map(lambda x: "Jul-Dec 2024" if x.year == 2024 else "Jan-Jun 2026")
        s = p.groupby(["category_name", "period"]).apply(lambda g: (g.decision == "decline").mean(), include_groups=False)
        s = s.reset_index(name="decline_rate")
        order = (s[s.period == "Jan-Jun 2026"].sort_values("decline_rate", ascending=False).category_name.tolist())
        line = alt.Chart(s).mark_line(color="#C9C0B6", strokeWidth=2).encode(
            x=alt.X("decline_rate:Q", title="Decline rate", axis=alt.Axis(format="%")), y=alt.Y("category_name:N", sort=order, title=None),
            detail="category_name:N")
        pts = alt.Chart(s).mark_circle(size=110, opacity=1).encode(
            x="decline_rate:Q", y=alt.Y("category_name:N", sort=order),
            color=alt.Color("period:N", title=None, scale=alt.Scale(domain=["Jul-Dec 2024", "Jan-Jun 2026"], range=["#B8ADA3", "#B02A1E"])),
            tooltip=[alt.Tooltip("category_name:N", title="Category"), alt.Tooltip("period:N", title="Period"),
                     alt.Tooltip("decline_rate:Q", title="Decline rate", format=".1%")])
        st.altair_chart((line + pts).properties(height=260), width="stretch", theme=None)

    with st.container(key="card_tbl"):
        st.markdown('<p class="mr-card-h">Segment table</p><p class="mr-card-s">Sortable. Same figures as the matrix.</p>',
                    unsafe_allow_html=True)
        t = seg[["category", "tier", "applications", "approval_rate", "refer_rate", "decline_rate", "avg_score", "avg_reserve_booked"]].copy()
        for c in ("approval_rate", "refer_rate", "decline_rate"):
            t[c] = t[c] * 100
        st.dataframe(t, hide_index=True, width="stretch", column_config={
            "category": "Category", "tier": "Credit tier", "applications": st.column_config.NumberColumn("Apps", format="%d"),
            "approval_rate": st.column_config.NumberColumn("Approve %", format="%.1f"),
            "refer_rate": st.column_config.NumberColumn("Refer %", format="%.1f"),
            "decline_rate": st.column_config.NumberColumn("Decline %", format="%.1f"),
            "avg_score": st.column_config.NumberColumn("Avg score", format="%.1f"),
            "avg_reserve_booked": st.column_config.NumberColumn("Reserve % booked", format="%.2f")})
