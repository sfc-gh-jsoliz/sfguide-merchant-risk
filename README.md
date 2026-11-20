# Merchant Risk & Underwriting — a Snow Pack

Score every new-merchant application — approve, refer, or decline — with an explainable 0–100 risk view, a reserve %, and an underwriting note the model is prevented from making up, all on Snowflake.

Owner: Javier Soliz · Last reviewed: November 2026

## What it shows

A Streamlit in Snowflake app for a payments processor / acquirer underwriting & risk-operations team. It generates a one-page underwriting note over a synthetic application/decision book — approval rate, average 0–100 risk score, decline rate, and reserve % by merchant category and credit tier — using only governed data, then a second pass fact-checks the draft against the allowed numbers and badges it **Verified** or **Needs review**. Each note is cross-referenced against an external payment-industry complaint backdrop (the free CFPB Consumer Complaint Database), attached by month and non-additive.

- A **gallery** of underwriting notes, each badged Verified / Needs review.
- A **sidebar** that generates a new note from the application book.
- A grounded draft written under DATA RULES (copy figures exactly, no estimates, no hedging), then verified.

## How it works

- The Streamlit app builds a **fact pack** (aggregated rows for the chosen segments and month) and calls Cortex **`AI_COMPLETE`** twice: once to write the note under strict DATA RULES, once to verify every claim against the fact pack.
- Setup also creates a Cortex **Agent** (`MERCHANT_RISK_AGENT`) and a Cortex **Analyst** semantic view (`MERCHANT_RISK_SV`) you can explore conversationally in Snowsight. These are provided for exploration and are **not** called by the Streamlit app.
- The app cross-references the real free **CFPB Consumer Complaint Database** (payment products only) as an external, non-additive industry backdrop — joined to the application book **by month only**. It is an industry signal, not this processor's own complaints. In sample mode the backdrop is synthetic so no listing is required.

## Prerequisites

- Snowflake Enterprise Edition or higher, in a region where Cortex AISQL and Cortex Agents are available.
- A Snowflake account with Cortex AI functions available in your region (`AI_COMPLETE`; defaults to `claude-sonnet-4-5` — change the `MODEL` parameter if your account differs).
- A role that can `CREATE DATABASE` and `CREATE WAREHOUSE` (setup provisions both in an isolated namespace).
- Streamlit in Snowflake enabled.
- Sample mode (`setup_synthetic.sql`) is fully synthetic — no Marketplace listing needed. Deploy mode (`setup.sql`) uses the **free, public** CFPB Complaint Database listing.

## Setup

1. **Sample (no listing):** run [`app/setup_synthetic.sql`](app/setup_synthetic.sql). It provisions the isolated database, schema, and warehouse and builds everything on a synthetic application/decision book **and** a synthetic CFPB backdrop. The app shows a synthetic-data banner.
2. **Deploy (real CFPB data):** in Snowsight → Marketplace, get the free **CFPB Complaint Database** (`CFPB_COMPLAINT`), then run [`app/setup.sql`](app/setup.sql). It keeps the synthetic book and swaps the CFPB backdrop to a view over the real `CFPB_COMPLAINT.DERIVED.CFPB_COMPLAINT_MAPPED` (payment products only). The app shows a *"Live backdrop"* banner.
3. **Deploy the app:** create a stage and the Streamlit app **inside `SNOWPACK_MERCHANT_RISK.CORE`** (e.g. `CREATE STAGE SNOWPACK_MERCHANT_RISK.CORE.APP_STAGE`, upload [`app/streamlit_app.py`](app/streamlit_app.py), then `CREATE STREAMLIT SNOWPACK_MERCHANT_RISK.CORE.MERCHANT_RISK_APP`), or paste it into a new Streamlit in Snowsight with `SNOWPACK_MERCHANT_RISK.CORE` as its location. Keeping the stage and app in this schema means [`app/teardown.sql`](app/teardown.sql) removes them with the database.
4. **Explore the agent:** Snowsight → AI & ML → Agents → **Merchant Risk Agent**.

Both scripts build the identical objects, so the app, semantic view, and agent are unchanged between modes.

## Customize with Cortex Code

Point [Cortex Code](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-code) at this pack and adapt it to your own underwriting program. A few prompts to start from:

- "Rewrite the underwriting-note DATA RULES in `streamlit_app.py` so the draft always states the decline rate and reserve % for the focus category before the overall takeaway."
- "Change the 0–100 risk score formula in `setup_synthetic.sql` to weight chargeback history and months-trading more heavily, and regenerate the synthetic decision book."
- "Adjust the reserve % logic so high-risk credit tiers get a higher reserve, then update the semantic view and the verifier so the new numbers are still fact-checked."
- "Swap the CFPB payment-complaint backdrop for a different product category and update the by-month join and the note's industry-backdrop wording."

## Objects created

| Object | Type | Purpose |
|---|---|---|
| `SNOWPACK_MERCHANT_RISK` | Database | Isolated namespace for this pack |
| `SNOWPACK_MERCHANT_RISK.CORE` | Schema | Holds all pack objects |
| `SNOWPACK_MERCHANT_RISK_WH` | Warehouse | XSMALL, auto-suspend 60s, dedicated compute |
| `MERCHANT_RISK_CATEGORY` | Table | Merchant-category dimension (MCC-aligned) with base risk weight |
| `MERCHANT_RISK_APPLICATION` | Table | Synthetic new-merchant underwriting applications |
| `MERCHANT_RISK_DECISION` | Table | Synthetic decisions (approve / refer / decline, risk score, reserve %) |
| `MERCHANT_RISK_CFPB_BENCHMARK` | Table (sample) / View (deploy) | Monthly CFPB complaint backdrop for payment products |
| `MERCHANT_RISK_BENCHMARK` | View | Portfolio by category / credit tier / decision / month + CFPB backdrop |
| `MERCHANT_RISK_DATA_SOURCE_INFO` | View | Marker indicating synthetic vs real backdrop mode |
| `MERCHANT_RISK_SV` | Semantic view | Cortex Analyst model over the benchmark (explore in Snowsight) |
| `MERCHANT_RISK_REPORTS` | Table | Persisted underwriting notes with verification status |
| `MERCHANT_RISK_AGENT` | Cortex Agent | Conversational Cortex Analyst agent over the semantic view |
| `streamlit_app.py` | Streamlit app | Generates and verifies underwriting notes |

## Cost & time

Setup runs in a few minutes on the dedicated **XSMALL** warehouse (auto-suspends at 60s). The only usage-based cost is Cortex `AI_COMPLETE` token consumption, incurred per note generated in the app (two calls each: draft + verify). The semantic view and agent cost nothing until queried.

## Known limitations

- The application/decision book is **synthetic** in both modes; swap `MERCHANT_RISK_APPLICATION` / `MERCHANT_RISK_DECISION` for your own intake (same columns) to score a real book.
- The CFPB backdrop is **non-additive** and joined **by month only** — it is an external payment-industry complaint signal, not this processor's own complaints.
- The static browser try page uses mocked AI responses (illustrative, not live inference).
- Illustrative example, not a production underwriting system — review and test before any real use.

## Cleanup

Run [`app/teardown.sql`](app/teardown.sql) to drop the `SNOWPACK_MERCHANT_RISK` database and the `SNOWPACK_MERCHANT_RISK_WH` warehouse. The free external CFPB listing, if mounted, is unaffected.

## Learn more

- [Snowflake Cortex AISQL (`AI_COMPLETE`)](https://docs.snowflake.com/en/user-guide/snowflake-cortex/aisql)
- [Cortex Agents](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-agents)
- [Cortex Analyst](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-analyst)
- [Streamlit in Snowflake](https://docs.snowflake.com/en/developer-guide/streamlit/about-streamlit)

## License

Apache 2.0 (see [`LICENSE`](LICENSE)). Illustrative example, as-is, not supported by Snowflake Support. This is not an official Snowflake product. Contains no customer data. Review and test before any production use.
