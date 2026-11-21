"""AI calls: the grounded underwriting note (draft + verify with AI_COMPLETE) and Ask the
agent (MERCHANT_RISK_AGENT, a Cortex Agent, via DATA_AGENT_RUN).

Sample mode replays responses captured from Live runs (sample/ai.json) after a
4-8 s staged wait, and the UI labels them "Sample AI response".
"""
import json
import random
import time
from pathlib import Path

from data import SCHEMA, session

MODEL = "claude-sonnet-4-5"
AGENT = f"{SCHEMA}.MERCHANT_RISK_AGENT"
SAMPLE_AI = Path(__file__).parent / "sample" / "ai.json"

SCOPES = {
    "ALL": "Whole book",
    "ELECTRONICS": "Electronics & Appliances", "RESTAURANTS": "Restaurants & Food Service",
    "FURNITURE": "Furniture & Home Furnishings", "APPAREL": "Clothing & Accessories",
    "HEALTH": "Health & Personal Care", "GROCERY": "Food & Beverage Stores",
}

QUESTIONS = [
    "Which merchant categories have the highest decline rate?",
    "How does the average risk score for C-Subprime compare to A-Prime?",
    "What was the approval rate by credit tier in the first half of 2026?",
    "Which month had the most declined Electronics & Appliances applications?",
]

RULES = (
    "You are a merchant-underwriting analyst at a payments processor. Write a concise underwriting risk note using ONLY the FACTS JSON.\n"
    "DATA RULES: use only numbers in FACTS and copy them exactly as written; risk_score is 0-100 (higher = riskier; approve < 40, refer 40-69.9, decline >= 70); "
    "rates are percentages; avg_reserve_pct_booked is the average reserve on approved and referred merchants; "
    "'first_6m' is Jul-Dec 2024 and 'last_6m' is Jan-Jun 2026; CFPB figures are an external payment-industry complaint backdrop, "
    "NOT this processor's own complaints, and are attached by month only; no estimates, no hedging, no outside benchmarks; missing = n/d. "
    "Do not name any real bank, processor or company.\n"
    "OUTPUT markdown starting with '# ', a one-line takeaway (highest-risk and lowest-approval segments), a table "
    "(segment | applications | approval % | decline % | avg risk | avg reserve % booked), 3 bullets (one on the first_6m vs last_6m change, "
    "one on decline reasons, one cross-referencing the CFPB backdrop), ending with '## Data Coverage'."
)


def sample_ai():
    return json.loads(SAMPLE_AI.read_text()) if SAMPLE_AI.exists() else {"notes": {}, "ask": {}}


def note_steps(scope):
    n = 720 if scope == "ALL" else 120
    seg = "6 categories and 4 credit tiers" if scope == "ALL" else "4 credit tiers"
    return [
        f"Reading {n} applications from MERCHANT_RISK_BENCHMARK and grouping by {seg}",
        "Adding first-6-month vs last-6-month change, decline reasons and the CFPB backdrop",
        f"Drafting the underwriting note with AI_COMPLETE ({MODEL}) under the DATA RULES",
        "Fact-checking every number against the fact pack with a second AI_COMPLETE pass",
        "Saving the note and verdict to MERCHANT_RISK_REPORTS",
    ]


ASK_STEPS = [
    "Sending the question to the Merchant Risk Agent (DATA_AGENT_RUN)",
    "Cortex Analyst writes SQL over the MERCHANT_RISK_SV semantic view",
    "Running the SQL on SNOWPACK_MERCHANT_RISK_WH",
    "Composing the answer from the result set",
]


def sample_wait(on_step, steps):
    """Spread a 4-8 s jittered wait over the staged steps (Sample mode only)."""
    total = random.uniform(4.0, 8.0)
    for i, s in enumerate(steps):
        on_step(i, s)
        time.sleep(total / len(steps))


# ---------------------------------------------------------------- note (Live)
_SEG = """
  SUM(application_count) AS applications,
  ROUND(100.0*SUM(approved_count)/NULLIF(SUM(application_count),0),1) AS approval_rate_pct,
  ROUND(100.0*SUM(referred_count)/NULLIF(SUM(application_count),0),1) AS refer_rate_pct,
  ROUND(100.0*SUM(declined_count)/NULLIF(SUM(application_count),0),1) AS decline_rate_pct,
  ROUND(SUM(risk_score_sum)/NULLIF(SUM(application_count),0),1) AS avg_risk_score,
  ROUND(SUM(IFF(decision <> 'decline', reserve_pct_sum, 0))
        / NULLIF(SUM(IFF(decision <> 'decline', application_count, 0)),0),2) AS avg_reserve_pct_booked"""


def _rows(q, params):
    df = session().sql(q, params=params).to_pandas()
    df.columns = [c.lower() for c in df.columns]
    return json.loads(df.to_json(orient="records"))


def fact_pack(scope):
    B = f"{SCHEMA}.MERCHANT_RISK_BENCHMARK"
    where, p = ("", []) if scope == "ALL" else ("WHERE category_code = ?", [scope])
    seg = ("category_name" if scope == "ALL" else "credit_tier")
    fp = {"scope": SCOPES[scope], "window": "2024-07-31 to 2026-06-30"}
    fp["segments"] = _rows(f"SELECT {seg} AS segment, {_SEG} FROM {B} {where} GROUP BY 1 ORDER BY 1", p)
    if scope == "ALL":
        fp["credit_tiers"] = _rows(f"SELECT credit_tier AS segment, {_SEG} FROM {B} GROUP BY 1 ORDER BY 1", [])
    fp["total"] = _rows(f"SELECT 'Total' AS segment, {_SEG} FROM {B} {where}", p)
    fp["periods"] = _rows(f"""
        SELECT {seg} AS segment, IFF(month_end <= '2024-12-31', 'first_6m', 'last_6m') AS period,
               SUM(application_count) AS applications,
               ROUND(100.0*SUM(declined_count)/NULLIF(SUM(application_count),0),1) AS decline_rate_pct,
               ROUND(SUM(risk_score_sum)/NULLIF(SUM(application_count),0),1) AS avg_risk_score
        FROM {B} WHERE (month_end <= '2024-12-31' OR month_end >= '2026-01-31') {('AND category_code = ?' if p else '')}
        GROUP BY 1, 2 ORDER BY 1, 2""", p)
    fp["decline_reasons"] = _rows(f"""
        SELECT d.decline_reason, COUNT(*) AS declines
        FROM {SCHEMA}.MERCHANT_RISK_DECISION d JOIN {SCHEMA}.MERCHANT_RISK_APPLICATION a USING (application_id)
        WHERE d.decision = 'decline' {('AND a.category_code = ?' if p else '')}
        GROUP BY 1 ORDER BY 2 DESC, 1""", p)
    fp["cfpb_backdrop"] = _rows(f"""
        SELECT IFF(cfpb_month <= '2024-12-31', 'first_6m', 'last_6m') AS period,
               ROUND(AVG(complaint_count),0) AS avg_monthly_complaints,
               ROUND(AVG(pct_monetary_relief),2) AS avg_pct_monetary_relief
        FROM {SCHEMA}.MERCHANT_RISK_CFPB_BENCHMARK
        WHERE cfpb_month BETWEEN '2024-07-31' AND '2024-12-31' OR cfpb_month BETWEEN '2026-01-31' AND '2026-06-30'
        GROUP BY 1 ORDER BY 1""", [])
    return fp


def complete(prompt):
    raw = session().sql("SELECT AI_COMPLETE(?, ?)", params=[MODEL, prompt]).collect()[0][0]
    # The string result can arrive JSON-encoded ("..." with escapes); decode it once.
    if isinstance(raw, str) and raw.startswith('"'):
        try:
            raw = json.loads(raw)
        except ValueError:
            pass
    return raw.strip()


def draft_note(fp):
    return complete(RULES + f"\n\nFACTS: {json.dumps(fp)}")


def verify(fp, draft):
    vp = (
        "You are a fact-checker. Compare the DRAFT against the FACTS JSON (only allowed source). Return ONLY a JSON object with keys "
        "reason (one sentence), status (exactly 'verified' if every number/claim is supported and there are no hedge words like "
        "likely/approximately/around/could, else exactly 'needs_review'), residual_hedges (int), "
        "edits (array of strings, each naming the unsupported or hedged claim). "
        "Rounding a FACTS number to the draft's display units (whole or one-decimal percentages, $M/$K) and simple differences "
        "between two FACTS numbers (for example a change in percentage points) count as supported; flag only wrong numbers, "
        "invented claims and hedges.\n\n"
        f"FACTS: {json.dumps(fp)}\n\nDRAFT:\n{draft}"
    )
    raw = complete(vp)
    v = None
    dec, i = json.JSONDecoder(), 0
    while True:  # the verifier can re-check itself and emit several objects; keep the last one
        s = raw.find("{", i)
        if s < 0:
            break
        try:
            v, i = dec.raw_decode(raw, s)
        except ValueError:
            i = s + 1
    if not isinstance(v, dict):
        v = {"status": "needs_review", "residual_hedges": None, "edits": ["The verifier output could not be parsed."]}
    v["status"] = "verified" if v.get("status") == "verified" else "needs_review"
    return v


def save_note(scope, draft, v, fp, latency_ms):
    session().sql(
        f"""INSERT INTO {SCHEMA}.MERCHANT_RISK_REPORTS
            (subject, draft_md, report_md, status, edits_applied, residual_hedges, edits, fact_pack, model, latency_ms)
            SELECT ?, ?, ?, ?, ?, ?, PARSE_JSON(?), PARSE_JSON(?), ?, ?""",
        params=[SCOPES[scope], draft, draft, v["status"], len(v.get("edits") or []), v.get("residual_hedges"),
                json.dumps(v.get("edits") or []), json.dumps(fp), MODEL, latency_ms],
    ).collect()


def run_note_live(scope, on_step):
    t0 = time.time()
    steps = note_steps(scope)
    on_step(0, steps[0])
    fp = fact_pack(scope)
    on_step(1, steps[1])
    on_step(2, steps[2])
    draft = draft_note(fp)
    on_step(3, steps[3])
    v = verify(fp, draft)
    latency = int((time.time() - t0) * 1000)
    on_step(4, steps[4])
    save_note(scope, draft, v, fp, latency)
    return {"scope": scope, "subject": SCOPES[scope], "markdown": draft, "status": v["status"],
            "edits": v.get("edits") or [], "residual_hedges": v.get("residual_hedges"),
            "fact_pack": fp, "model": MODEL, "latency_ms": latency}


# ---------------------------------------------------------------- ask the agent (Live)
def parse_agent(raw):
    """Final answer = text and table blocks after the last tool block; SQL from the tool result."""
    j = json.loads(raw) if isinstance(raw, str) else raw
    content = j.get("content", [])
    last_tool = max([i for i, b in enumerate(content) if b.get("type") in ("tool_use", "tool_result")], default=-1)
    text, table, sql = [], None, None
    for b in content:
        if b.get("type") == "tool_result":
            for c in b["tool_result"].get("content", []):
                if isinstance(c.get("json"), dict) and c["json"].get("sql"):
                    sql = c["json"]["sql"]
    for b in content[last_tool + 1:]:
        if b.get("type") == "text":
            text.append(b["text"])
        elif b.get("type") == "table" and table is None:
            rs = b["table"].get("result_set", {})
            cols = [c["name"] for c in rs.get("resultSetMetaData", {}).get("rowType", [])]
            table = {"columns": cols, "rows": rs.get("data", [])}
    return {"text": "\n\n".join(text).strip(), "sql": sql, "table": table}


def ask_live(question, on_step):
    t0 = time.time()
    on_step(0, ASK_STEPS[0])
    body = json.dumps({"messages": [{"role": "user", "content": [{"type": "text", "text": question}]}], "stream": False})
    raw = session().sql("SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(?, ?)", params=[AGENT, body]).collect()[0][0]
    for i in (1, 2, 3):
        on_step(i, ASK_STEPS[i])
    out = parse_agent(raw)
    out.update({"question": question, "latency_ms": int((time.time() - t0) * 1000)})
    return out
