"""Portfolio: the underwriting desk's overview of the application book."""
import altair as alt
import pandas as pd
import streamlit as st

import brand
import data
from views.common import cap, decision_scale, load, theme


def render(mode):
    theme()
    df, cf, src = load(mode)
    m = data.monthly(df)
    last6, prev6 = df[df.month >= "2026-01-01"], df[(df.month >= "2025-07-01") & (df.month < "2026-01-01")]
    a, b = data.rates(last6), data.rates(prev6)

    st.markdown(brand.header(
        "Portfolio", f"{len(df):,} new-merchant applications, July 2024 to June 2026, scored 0-100 and decided "
        "approve / refer / decline. Tiles compare Jan-Jun 2026 with Jul-Dec 2025.",
        cap(mode, "MERCHANT_RISK_BOOK view"), mode), unsafe_allow_html=True)

    def pp(x, y):
        return f"{(x - y) * 100:+.1f} pp vs H2 2025"
    tiles = [
        brand.kpi("Applications, H1 2026", brand.counter("", a["applications"]),
                  f'<span class="flat">{brand.usd(a["volume"])} requested / month</span>', list(m.applications)),
        brand.kpi("Approval rate", brand.num(a["approval_rate"] * 100, 1, "", "%"),
                  brand.delta(a["approval_rate"] - b["approval_rate"], pp(a["approval_rate"], b["approval_rate"])),
                  list(m.approval_rate)),
        brand.kpi("Decline rate", brand.num(a["decline_rate"] * 100, 1, "", "%"),
                  brand.delta(a["decline_rate"] - b["decline_rate"], pp(a["decline_rate"], b["decline_rate"]), good_when_up=False),
                  list(m.decline_rate)),
        brand.kpi("Average risk score", brand.num(a["avg_score"], 1),
                  brand.delta(a["avg_score"] - b["avg_score"], f'{a["avg_score"] - b["avg_score"]:+.1f} vs H2 2025', good_when_up=False),
                  list(m.avg_score)),
        brand.kpi("Avg reserve, booked", brand.num(a["avg_reserve_booked"], 2, "", "%"),
                  brand.delta(a["avg_reserve_booked"] - b["avg_reserve_booked"],
                              f'{a["avg_reserve_booked"] - b["avg_reserve_booked"]:+.2f} pp vs H2 2025', good_when_up=False),
                  list(m.avg_reserve_booked)),
    ]
    st.markdown(f'<div class="mr-kpis">{"".join(tiles)}</div>', unsafe_allow_html=True)

    with st.container(key="card_rail"):
        st.markdown('<p class="mr-card-h">Every application on the threshold rail</p><p class="mr-card-s">'
                    'One tick per application at its risk score. Under 40 approves, 40 to 69.9 refers to an underwriter, 70 and over declines.</p>',
                    unsafe_allow_html=True)
        st.markdown(brand.rail(df.risk_score, df.decision), unsafe_allow_html=True)
        n = df.decision.value_counts()
        st.markdown('<div class="mr-legend">' + "".join(
            f'<span><i style="background:{brand.DEC_COLORS[d]}"></i>{d.capitalize()} <b style="font-family:var(--mono)">{n.get(d, 0)}</b> '
            f'({n.get(d, 0) / len(df) * 100:.1f}%)</span>' for d in data.DECISIONS) + "</div>", unsafe_allow_html=True)

    seg = df.groupby("category_name").apply(lambda g: pd.Series(data.rates(g)), include_groups=False)
    worst = seg.decline_rate.idxmax()
    best = seg.approval_rate.idxmax()
    el = df[df.category_code == "ELECTRONICS"]
    el_a, el_b = data.rates(el[el.month >= "2026-01-01"]), data.rates(el[el.month < "2026-01-01"])
    st.markdown(
        f'<div class="mr-insight"><b>On the desk.</b> {brand.esc(worst)} carries the highest decline rate '
        f'({brand.pc(seg.decline_rate[worst])}); {brand.esc(best)} the highest approval rate ({brand.pc(seg.approval_rate[best])}). '
        f'Electronics chargeback history has drifted up in 2026: its decline rate went from {brand.pc(el_b["decline_rate"])} '
        f'(Jul 2024 to Dec 2025) to {brand.pc(el_a["decline_rate"])} (Jan to Jun 2026). Open <b>Applications</b> to see why any one '
        f'merchant scored as it did, or <b>Underwriting notes</b> for a verified write-up.</div>', unsafe_allow_html=True)

    left, right = st.columns([2, 1], gap="medium")
    with left.container(key="card_mix"):
        st.markdown('<p class="mr-card-h">Decision mix by month</p><p class="mr-card-s">Applications per month by decision. Hover for counts.</p>',
                    unsafe_allow_html=True)
        long = m.melt(id_vars=["month"], value_vars=data.DECISIONS, var_name="decision", value_name="count")
        long["order"] = long.decision.map({d: i for i, d in enumerate(data.DECISIONS)})
        chart = alt.Chart(long).mark_bar(size=14, cornerRadiusTopLeft=2, cornerRadiusTopRight=2).encode(
            x=alt.X("month:T", title=None, axis=alt.Axis(format="%b %y", labelAngle=0, tickCount=8)),
            y=alt.Y("count:Q", title="Applications", stack="zero"),
            color=alt.Color("decision:N", title=None, scale=decision_scale()),
            order=alt.Order("order:Q"),
            tooltip=[alt.Tooltip("month:T", title="Month-end", format="%B %Y"), alt.Tooltip("decision:N", title="Decision"),
                     alt.Tooltip("count:Q", title="Applications")],
        ).properties(height=290)
        st.altair_chart(chart, width="stretch", theme=None)
    with right.container(key="card_reasons"):
        st.markdown('<p class="mr-card-h">Why applications decline</p><p class="mr-card-s">First matching rule per declined application.</p>',
                    unsafe_allow_html=True)
        r = df[df.decision == "decline"].decline_reason.value_counts()
        top = r.max()
        items = "".join(
            f'<li><span>{brand.esc(k)}</span><span class="bar"><i style="left:0;width:{v / top * 100:.0f}%;background:{brand.T["decline"]}"></i></span>'
            f'<span class="n">{v}</span></li>' for k, v in r.items())
        st.markdown(f'<ul class="mr-fx">{items}</ul>', unsafe_allow_html=True)
        st.markdown(f'<p class="mr-card-s" style="margin-top:.6rem">{int(r.sum())} declines in total.</p>', unsafe_allow_html=True)

    with st.container(key="card_cfpb"):
        label = "real CFPB Complaint Database" if src == "marketplace" else "synthetic CFPB-style series"
        st.markdown(f'<p class="mr-card-h">Industry backdrop: payment-product complaints</p><p class="mr-card-s">'
                    f'Monthly complaints ({label}, dashed) against this book\'s decline rate. The backdrop is an external, '
                    'non-additive signal joined by month only; it is not this processor\'s complaints.</p>', unsafe_allow_html=True)
        j = m[["month", "decline_rate"]].merge(cf[["month", "complaint_count", "pct_monetary_relief"]], on="month", how="left")
        j["decline_pct"] = j.decline_rate * 100
        base = alt.Chart(j).encode(x=alt.X("month:T", title=None, axis=alt.Axis(format="%b %y", labelAngle=0, tickCount=8)))
        tip = [alt.Tooltip("month:T", title="Month-end", format="%B %Y"), alt.Tooltip("decline_pct:Q", title="Decline rate %", format=".1f"),
               alt.Tooltip("complaint_count:Q", title="CFPB complaints", format=",.0f"),
               alt.Tooltip("pct_monetary_relief:Q", title="% monetary relief", format=".2f")]
        l1 = base.mark_line(color=brand.T["ox500"], strokeWidth=2.2, point=alt.OverlayMarkDef(size=26, filled=True)).encode(
            y=alt.Y("decline_pct:Q", title="Decline rate (%)", axis=alt.Axis(titleColor=brand.T["ox500"])), tooltip=tip)
        l2 = base.mark_line(color=brand.T["steel"], strokeWidth=2, strokeDash=[5, 4]).encode(
            y=alt.Y("complaint_count:Q", title="CFPB complaints / month", scale=alt.Scale(zero=False),
                    axis=alt.Axis(titleColor=brand.T["steel"])), tooltip=tip)
        st.altair_chart(alt.layer(l1, l2).resolve_scale(y="independent").properties(height=230), width="stretch", theme=None)
        st.markdown('<div class="mr-legend"><span><i style="background:#7D2A3C"></i>Decline rate (this book)</span>'
                    '<span><i style="background:#36587A"></i>CFPB payment complaints (backdrop)</span></div>', unsafe_allow_html=True)
