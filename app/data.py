"""Data layer: Sample (bundled CSVs) or Live (Snowflake), same shape either way.

Live never falls back to Sample: a failed query raises, and the page shows the error.
"""
import os
from pathlib import Path

import pandas as pd
import streamlit as st

DB = "SNOWPACK_MERCHANT_RISK"
SCHEMA = f"{DB}.CORE"
WAREHOUSE = "SNOWPACK_MERCHANT_RISK_WH"
ROLE = "MERCHANT_RISK_ROLE"
SAMPLE_DIR = Path(__file__).parent / "sample"
LIVE_ENV = ("SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PRIVATE_KEY_PATH")

DECISIONS = ["approve", "refer", "decline"]
TIERS = ["A-Prime", "B-NearPrime", "C-Subprime", "D-HighRisk"]
TIER_STEP = {t: i for i, t in enumerate(TIERS)}
FACTORS = [("f_category", "Category base risk"), ("f_chargebacks", "Chargeback history"),
           ("f_credit_tier", "Credit tier"), ("f_tenure", "Years trading"),
           ("f_prior_processor", "Switching from a prior processor")]
NUM = ["requested_monthly_volume", "years_in_business", "prior_processor_flag", "chargeback_history_bps",
       "risk_score", "reserve_pct"] + [f for f, _ in FACTORS]


def in_snowflake():
    """True when running as Streamlit in Snowflake (an active session exists)."""
    try:
        from snowflake.snowpark.context import get_active_session
        get_active_session()
        return True
    except Exception:
        return False


def live_configured():
    return in_snowflake() or all(os.environ.get(k) for k in LIVE_ENV)


@st.cache_resource(show_spinner=False)
def session():
    """Snowpark session: the app's own in Snowflake, key-pair auth when run locally."""
    if in_snowflake():
        from snowflake.snowpark.context import get_active_session
        return get_active_session()
    from snowflake.snowpark import Session
    return Session.builder.configs({
        "account": os.environ["SNOWFLAKE_ACCOUNT"],
        "user": os.environ["SNOWFLAKE_USER"],
        "authenticator": "SNOWFLAKE_JWT",
        "private_key_file": os.environ["SNOWFLAKE_PRIVATE_KEY_PATH"],
        "role": os.environ.get("SNOWFLAKE_ROLE", ROLE),
        "warehouse": os.environ.get("SNOWFLAKE_WAREHOUSE", WAREHOUSE),
        "database": DB,
        "schema": "CORE",
    }).create()


def sql_df(q, params=None):
    df = session().sql(q, params=params or []).to_pandas()
    df.columns = [c.lower() for c in df.columns]
    return df


def _book_from_csv():
    a = pd.read_csv(SAMPLE_DIR / "applications.csv", dtype={"mcc": str})
    d = pd.read_csv(SAMPLE_DIR / "decisions.csv")
    c = pd.read_csv(SAMPLE_DIR / "categories.csv", dtype={"mcc": str})
    df = a.merge(d, on="application_id").merge(c[["category_code", "base_risk"]], on="category_code")
    # Same factor columns as the MERCHANT_RISK_SCORE_FACTORS view
    df["f_category"] = df["base_risk"]
    df["f_chargebacks"] = df["chargeback_history_bps"] / 10
    df["f_credit_tier"] = df["credit_tier"].map(TIER_STEP) * 8
    df["f_tenure"] = -df["years_in_business"].clip(upper=15) * 1.2
    df["f_prior_processor"] = -df["prior_processor_flag"] * 5
    df["decline_reason"] = df["decline_reason"].fillna("")
    return df.drop(columns=["base_risk"])


@st.cache_data(show_spinner=False, ttl=600)
def book(mode):
    """One row per application (MERCHANT_RISK_BOOK in Live)."""
    if mode == "Live":
        df = sql_df(f"""SELECT application_id, merchant_name, mcc, category_code, category_name, credit_tier,
                               requested_monthly_volume, years_in_business, prior_processor_flag,
                               chargeback_history_bps, month_end::string AS month_end, decision, risk_score,
                               COALESCE(decline_reason, '') AS decline_reason, reserve_pct,
                               f_category, f_chargebacks, f_credit_tier, f_tenure, f_prior_processor
                        FROM {SCHEMA}.MERCHANT_RISK_BOOK ORDER BY application_id""")
    else:
        df = _book_from_csv()
    for col in NUM:
        df[col] = pd.to_numeric(df[col]).astype(float)
    df["month"] = pd.to_datetime(df["month_end"])
    return df.sort_values("application_id").reset_index(drop=True)


@st.cache_data(show_spinner=False, ttl=600)
def cfpb(mode):
    """Monthly CFPB payment-complaint backdrop and its source mode."""
    if mode == "Live":
        df = sql_df(f"""SELECT cfpb_month::string AS cfpb_month, complaint_count, pct_monetary_relief, pct_timely_response
                        FROM {SCHEMA}.MERCHANT_RISK_CFPB_BENCHMARK
                        WHERE cfpb_month BETWEEN '2024-07-31' AND '2026-06-30' ORDER BY cfpb_month""")
        src = sql_df(f"SELECT mode FROM {SCHEMA}.MERCHANT_RISK_DATA_SOURCE_INFO")["mode"].iloc[0]
    else:
        df = pd.read_csv(SAMPLE_DIR / "cfpb_monthly.csv")
        src = "synthetic"
    for col in ("complaint_count", "pct_monetary_relief", "pct_timely_response"):
        df[col] = pd.to_numeric(df[col]).astype(float)
    df["month"] = pd.to_datetime(df["cfpb_month"])
    return df, src


def rates(g):
    """Approval / refer / decline rate, average score and booked reserve for a group of applications."""
    n = len(g)
    booked = g[g.decision != "decline"]
    return {
        "applications": n,
        "approval_rate": (g.decision == "approve").mean() if n else 0.0,
        "refer_rate": (g.decision == "refer").mean() if n else 0.0,
        "decline_rate": (g.decision == "decline").mean() if n else 0.0,
        "avg_score": g.risk_score.mean() if n else 0.0,
        "avg_reserve_booked": booked.reserve_pct.mean() if len(booked) else 0.0,
        "volume": g.requested_monthly_volume.sum(),
    }


def monthly(df):
    rows = []
    for m, g in df.groupby("month"):
        r = rates(g)
        r["month"] = m
        for d in DECISIONS:
            r[d] = int((g.decision == d).sum())
        rows.append(r)
    return pd.DataFrame(rows).sort_values("month").reset_index(drop=True)


def segments(df):
    rows = []
    for (cat, tier), g in df.groupby(["category_name", "credit_tier"]):
        r = rates(g)
        r.update({"category": cat, "tier": tier})
        rows.append(r)
    return pd.DataFrame(rows)


@st.cache_data(show_spinner=False, ttl=30)
def saved_notes(mode):
    if mode != "Live":
        return None
    return sql_df(f"""SELECT run_id, subject, status, edits_applied, residual_hedges, report_md, edits,
                             fact_pack, model, latency_ms, created_at::string AS created_at
                      FROM {SCHEMA}.MERCHANT_RISK_REPORTS ORDER BY created_at DESC LIMIT 24""")
