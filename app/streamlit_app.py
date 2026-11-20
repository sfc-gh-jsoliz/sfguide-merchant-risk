import json
import streamlit as st
from snowflake.snowpark.context import get_active_session

st.set_page_config(page_title="Merchant Risk & Underwriting", layout="wide")

SCHEMA = "SNOWPACK_MERCHANT_RISK.CORE"
MODEL = "claude-sonnet-4-5"
session = get_active_session()
_rerun = getattr(st, "rerun", getattr(st, "experimental_rerun", lambda: None))
BADGE = {"verified": "✅ Verified", "needs_review": "⚠️ Needs review"}


def sql_df(q, p=None):
    df = session.sql(q, params=p or []).to_pandas()
    df.columns = [c.lower() for c in df.columns]
    return df


def data_mode():
    try:
        r = session.sql(f"SELECT mode, note FROM {SCHEMA}.MERCHANT_RISK_DATA_SOURCE_INFO").collect()[0]
        return r[0], r[1]
    except Exception:
        return "unknown", ""


def load_reports():
    return sql_df(f"SELECT run_id, subject, status, edits_applied, residual_hedges, report_md, created_at FROM {SCHEMA}.MERCHANT_RISK_REPORTS ORDER BY created_at DESC")


def fact_pack():
    return session.sql(f"""
        WITH w AS (SELECT MIN(month_end) a, MAX(month_end) z FROM {SCHEMA}.MERCHANT_RISK_BENCHMARK),
        agg AS (
          SELECT category_name, credit_tier, month_end,
                 SUM(application_count) AS applications,
                 ROUND(100.0*SUM(approved_count)/NULLIF(SUM(application_count),0),1) AS approval_rate_pct,
                 ROUND(100.0*SUM(declined_count)/NULLIF(SUM(application_count),0),1) AS decline_rate_pct,
                 ROUND(SUM(risk_score_sum)/NULLIF(SUM(application_count),0),1) AS avg_risk_score,
                 ROUND(SUM(reserve_pct_sum)/NULLIF(SUM(application_count),0),2) AS avg_reserve_pct,
                 MAX(cfpb_complaint_count) AS cfpb_complaints,
                 MAX(cfpb_pct_monetary_relief) AS cfpb_pct_monetary_relief
          FROM {SCHEMA}.MERCHANT_RISK_BENCHMARK b JOIN w ON b.month_end IN (w.a, w.z)
          GROUP BY category_name, credit_tier, month_end
        )
        SELECT ARRAY_AGG(OBJECT_CONSTRUCT(
          'category', category_name, 'credit_tier', credit_tier, 'month', month_end::string,
          'applications', applications, 'approval_rate_pct', approval_rate_pct,
          'decline_rate_pct', decline_rate_pct, 'avg_risk_score', avg_risk_score,
          'avg_reserve_pct', avg_reserve_pct, 'cfpb_complaints', cfpb_complaints,
          'cfpb_pct_monetary_relief', cfpb_pct_monetary_relief))
        FROM agg
    """).collect()[0][0]


def draft_note(fp):
    rules = (
        "You are a merchant-underwriting analyst. Write a concise risk note using ONLY the FACTS JSON.\n"
        "DATA RULES: use only numbers in FACTS, copy exactly; risk_score is 0-100 (higher = riskier); rates are percentages; "
        "dollars are USD, express $B/$M; CFPB figures are an external payment-industry complaint backdrop, NOT this processor's own complaints; "
        "no estimates, no hedging, no outside benchmarks; missing = n/d.\n"
        "OUTPUT markdown starting with '# ', a one-line takeaway (highest-risk / lowest-approval segments), a table "
        "(category | credit tier | applications | approval % | avg risk | avg reserve %), 3 bullets (one cross-referencing the CFPB backdrop), ending with '## Data Coverage'."
    )
    return session.sql("SELECT AI_COMPLETE(?, ?)", params=[MODEL, rules + f"\n\nFACTS: {fp}"]).collect()[0][0]


def verify(fp, draft):
    vp = (
        "You are a fact-checker. Compare the DRAFT against the FACTS JSON (only allowed source). Return ONLY a JSON object with keys "
        "status ('verified' if every number/claim is supported and no hedge words like likely/approximately/around/could, else 'needs_review'), "
        "residual_hedges (int), edits (array of strings).\n\n" + f"FACTS: {fp}\n\nDRAFT:\n{draft}"
    )
    raw = session.sql("SELECT AI_COMPLETE(?, ?)", params=[MODEL, vp]).collect()[0][0]
    s, e = raw.find("{"), raw.rfind("}")
    try:
        return json.loads(raw[s:e + 1])
    except Exception:
        return {"status": "needs_review", "residual_hedges": None, "edits": ["unparseable verifier output"]}


st.title("Merchant Risk & Underwriting")
st.caption("Score new-merchant applications (approve / refer / decline, risk score, reserve %) and cross-reference the CFPB complaint backdrop for payment products.")
_mode, _note = data_mode()
if _mode == "synthetic":
    st.warning("Sample mode — synthetic CFPB backdrop. " + _note)
elif _mode == "marketplace":
    st.info("Live backdrop — " + _note)

if "view" not in st.session_state:
    st.session_state["view"] = "gallery"

with st.sidebar:
    st.subheader("Generate a note")
    st.caption("Benchmarks the application book by segment and writes a verified underwriting risk note.")
    if st.button("Run underwriting analysis", type="primary", use_container_width=True):
        with st.spinner("Fact pack → grounded draft → verify (~20-40s)..."):
            fp = fact_pack()
            draft = draft_note(fp)
            v = verify(fp, draft)
            status = "verified" if v.get("status") == "verified" else "needs_review"
            session.sql(
                f"INSERT INTO {SCHEMA}.MERCHANT_RISK_REPORTS (subject, draft_md, report_md, status, edits_applied, residual_hedges) SELECT ?, ?, ?, ?, ?, ?",
                params=["Merchant risk & underwriting", draft, draft, status, len(v.get("edits", [])), v.get("residual_hedges")],
            ).collect()
        st.success(f"Done — {BADGE[status]}")
        st.session_state["view"] = "gallery"
        _rerun()

if st.session_state["view"].startswith("report:"):
    run_id = st.session_state["view"].split(":", 1)[1]
    rpt = load_reports()
    row = rpt[rpt["run_id"] == run_id]
    if st.button("← Back to gallery"):
        st.session_state["view"] = "gallery"
        _rerun()
    if not row.empty:
        r = row.iloc[0]
        st.markdown(f"**{BADGE.get(r['status'], r['status'])}**  &nbsp; residual hedges: {r['residual_hedges']}  |  flagged: {r['edits_applied']}")
        st.divider()
        st.markdown(r["report_md"])
else:
    reports = load_reports()
    if reports.empty:
        st.info("No notes yet. Use the sidebar to generate one.")
    else:
        cols = st.columns(3)
        for i, (_, r) in enumerate(reports.iterrows()):
            with cols[i % 3]:
                c = st.container()
                c.markdown(f"**{BADGE.get(r['status'], r['status'])}**")
                c.markdown(f"**{r['subject']}**")
                c.caption(f"{str(r['created_at'])[:16]} · {r['edits_applied']} flagged")
                if c.button("Open report", key=f"open_{r['run_id']}", use_container_width=True):
                    st.session_state["view"] = f"report:{r['run_id']}"
                    _rerun()
                c.markdown("---")
