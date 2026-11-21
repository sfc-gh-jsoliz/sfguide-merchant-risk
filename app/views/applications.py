"""Applications: the review queue, with an explainable score for each merchant."""
import streamlit as st

import brand
import data
from views.common import cap, load

SORTS = {"Risk score, highest first": ("risk_score", False), "Risk score, lowest first": ("risk_score", True),
         "Newest first": ("month_end", False), "Requested volume, highest first": ("requested_monthly_volume", False),
         "Chargebacks, highest first": ("chargeback_history_bps", False)}


def factor_bars(r):
    rows = []
    for f, label in data.FACTORS:
        v = float(r[f])
        w = min(abs(v), 100)
        color = brand.T["decline"] if v > 0 else brand.T["approve"]
        rows.append(f'<li><span>{brand.esc(label)}</span><span class="bar"><i style="left:0;width:{w:.0f}%;background:{color}"></i></span>'
                    f'<span class="n">{v:+.1f}</span></li>')
    raw = sum(float(r[f]) for f, _ in data.FACTORS)
    clamp = "" if 0 <= raw <= 100 else f' (raw {raw:.1f}, clamped to 0-100)'
    rows.append(f'<li style="border-bottom:0"><b>Risk score</b><span></span><span class="n"><b>{r.risk_score:.1f}</b></span></li>')
    return f'<ul class="mr-fx">{"".join(rows)}</ul><p class="mr-card-s">Red adds risk, green reduces it{clamp}.</p>'


def detail(r, mode):
    reason = r.decline_reason or ("Under the 40-point approval threshold" if r.decision == "approve"
                                  else "Between 40 and 70: an underwriter reviews before booking")
    reserve = "No reserve: declined" if r.decision == "decline" else f"{r.reserve_pct:.2f}% rolling reserve"
    st.markdown(f'<p class="mr-card-s" style="margin:0">{brand.esc(r.application_id)} · {r.month:%B %Y}</p>'
                f'<p class="mr-card-h" style="font-size:1.08rem">{brand.esc(r.merchant_name)}</p>'
                f'<div style="display:flex;gap:.4rem;flex-wrap:wrap;margin:.3rem 0 .4rem">{brand.pill(r.decision)}'
                f'<span class="mr-pill n">{brand.esc(r.credit_tier)}</span><span class="mr-pill n">MCC {brand.esc(r.mcc)}</span></div>',
                unsafe_allow_html=True)
    st.markdown(brand.rail([], [], marker=r.risk_score, h=56, W=420), unsafe_allow_html=True)
    st.markdown(f'<div class="mr-facts"><div><span>Requested volume / month</span><b>{brand.usd(r.requested_monthly_volume)}</b></div>'
                f'<div><span>Chargebacks</span><b>{r.chargeback_history_bps:.0f} bps</b></div>'
                f'<div><span>Years trading</span><b>{r.years_in_business:.0f}</b></div>'
                f'<div><span>Prior processor</span><b>{"Yes" if r.prior_processor_flag else "No"}</b></div>'
                f'<div><span>Reserve</span><b>{"0.00%" if r.decision == "decline" else f"{r.reserve_pct:.2f}%"}</b></div>'
                f'<div><span>Category</span><b style="font-family:var(--sans);font-size:.82rem">{brand.esc(r.category_name)}</b></div></div>',
                unsafe_allow_html=True)
    st.markdown('<p class="mr-card-h" style="font-size:.9rem">Why it scored this way</p>', unsafe_allow_html=True)
    st.markdown(factor_bars(r), unsafe_allow_html=True)
    st.markdown(f'<div class="mr-insight" style="margin-bottom:.4rem"><b>{r.decision.capitalize()}.</b> {brand.esc(reason)}. {brand.esc(reserve)}.</div>'
                f'<div class="mr-src">Source: <code>{"MERCHANT_RISK_BOOK" if mode == "Live" else "app/sample"}</code> · factors from '
                '<code>MERCHANT_RISK_SCORE_FACTORS</code></div>', unsafe_allow_html=True)


def render(mode):
    df, _, _ = load(mode)
    st.markdown(brand.header(
        "Applications", "The review queue. Filter and sort the book, then select a row to see how its score was built.",
        cap(mode, "MERCHANT_RISK_BOOK view"), mode), unsafe_allow_html=True)

    with st.container(key="card_filters"):
        c1, c2, c3, c4 = st.columns([1.4, 1.2, 1.2, 1.2])
        q = c1.text_input("Search", placeholder="Merchant or application ID", key="q")
        dec = c2.multiselect("Decision", data.DECISIONS, format_func=str.capitalize, key="f_dec")
        cats = c3.multiselect("Category", sorted(df.category_name.unique()), key="f_cat")
        tiers = c4.multiselect("Credit tier", data.TIERS, key="f_tier")
        c5, c6 = st.columns([2, 1.4])
        lo, hi = c5.slider("Risk score", 0, 100, (0, 100), key="f_score")
        sort = c6.selectbox("Sort", list(SORTS), key="f_sort")

    f = df
    if q:
        f = f[f.merchant_name.str.contains(q, case=False) | f.application_id.str.contains(q, case=False)]
    if dec:
        f = f[f.decision.isin(dec)]
    if cats:
        f = f[f.category_name.isin(cats)]
    if tiers:
        f = f[f.credit_tier.isin(tiers)]
    f = f[(f.risk_score >= lo) & (f.risk_score <= hi)]
    col, asc = SORTS[sort]
    f = f.sort_values([col, "application_id"], ascending=[asc, True]).reset_index(drop=True)

    counts = f.decision.value_counts()
    st.markdown('<div style="display:flex;gap:.5rem;flex-wrap:wrap;align-items:center;margin:.2rem 0 .6rem">'
                f'<span style="font-size:.85rem;color:var(--ink2)"><b>{len(f)}</b> of {len(df)} applications</span>'
                + "".join(f'{brand.pill(d)}<span style="font-family:var(--mono);font-size:.8rem;margin-right:.4rem">{counts.get(d, 0)}</span>'
                          for d in data.DECISIONS) + "</div>", unsafe_allow_html=True)

    if f.empty:
        st.markdown('<div class="mr-card mr-empty"><b>No applications match</b>Clear a filter or widen the score range.</div>',
                    unsafe_allow_html=True)
        return

    left, right = st.columns([1.55, 1], gap="medium")
    view = f[["application_id", "merchant_name", "credit_tier", "risk_score", "decision", "reserve_pct",
              "chargeback_history_bps", "years_in_business", "month_end"]].copy()
    view["decision"] = view.decision.str.capitalize()
    soft = {"Approve": (brand.T["approveSoft"], brand.T["approve"]), "Refer": (brand.T["referSoft"], brand.T["refer"]),
            "Decline": (brand.T["declineSoft"], brand.T["decline"])}
    styled = view.style.map(lambda v: f"background-color:{soft[v][0]};color:{soft[v][1]};font-weight:600", subset=["decision"])
    with left.container(key="card_table"):
        ev = st.dataframe(
            styled, hide_index=True, width="stretch", height=520, on_select="rerun", selection_mode="single-row",
            key="queue",
            column_config={
                "application_id": st.column_config.TextColumn("ID", width="small"),
                "merchant_name": st.column_config.TextColumn("Merchant"),
                "credit_tier": st.column_config.TextColumn("Tier", width="small"),
                "risk_score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%.1f", width="small"),
                "decision": st.column_config.TextColumn("Decision", width="small"),
                "reserve_pct": st.column_config.NumberColumn("Reserve %", format="%.2f", width="small"),
                "chargeback_history_bps": st.column_config.NumberColumn("CB bps", format="%d", width="small"),
                "years_in_business": st.column_config.NumberColumn("Years", format="%d", width="small"),
                "month_end": st.column_config.TextColumn("Month", width="small"),
            })
    sel = ev.selection.rows if ev and ev.selection else []
    with right.container(key="card_detail"):
        if sel:
            detail(f.iloc[sel[0]], mode)
        else:
            st.markdown('<p class="mr-cap" style="margin-bottom:.5rem">Showing the top row. Select any row to open it.</p>',
                        unsafe_allow_html=True)
            detail(f.iloc[0], mode)
