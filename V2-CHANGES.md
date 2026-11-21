# Merchant Risk & Underwriting: v2 changes

This branch rebuilds the pack to the Snow Packs v2 bar (see [`COCO-V2-INSTRUCTIONS.md`](COCO-V2-INSTRUCTIONS.md)). What stays the same: the use case (new-merchant underwriting at a processor or acquirer), the six categories, the risk-score formula, the 40 / 70 thresholds, the decline reasons and reserve rules, the CFPB payment-complaint backdrop joined by month, the grounded-note loop (fact pack → `AI_COMPLETE` draft → `AI_COMPLETE` verify), the `MERCHANT_RISK_SV` semantic view and `MERCHANT_RISK_AGENT`, the Streamlit stack, the object names, the notebook and the owner line. The app is titled with the pack's plain name; there is no product name.

## Screen by screen

### App shell (new)
- **Before:** a Streamlit title, a mode banner and a sidebar button.
- **After:** an oxblood sidebar with the gauge mark, the title, a Sample/Live switch, an environment badge, a role chip and five screens. Tokens, fonts and motion follow [`docs/DESIGN.md`](docs/DESIGN.md). The environment badge repeats in every page header so the mode is visible on phones, where the sidebar collapses behind the menu button.
- **Why:** v2 asks for a branded product shell with an always-visible mode. The old app had no Sample mode; it needed a Snowflake session to start.

### Portfolio (new)
- KPI tiles (applications, approval rate, decline rate, average score, average booked reserve) comparing Jan–Jun 2026 with Jul–Dec 2025, with sparklines and count-up; the **threshold rail** with every application as a tick; an "On the desk" insight; decision mix by month; decline reasons; and the CFPB backdrop against the book's decline rate (dashed, labeled as external and non-additive).
- **Why:** the old app opened on a list of saved notes, so a first-time reader saw no numbers until they ran the AI.

### Applications (new)
- A review queue with search, decision, category, tier and score filters, five sort orders, decision-coloured cells and a score bar. Selecting a row opens a detail panel: the score on the threshold rail, the merchant's facts, a bar per scoring factor, and the decision reason and reserve.
- **Why:** the pack promises an *explainable* score; this shows the explanation for every merchant. Backed by a new `MERCHANT_RISK_SCORE_FACTORS` view.

### Segments (new)
- Category × credit tier heatmap (decline rate, approval rate, average score or booked reserve), the score distribution coloured by decision with the thresholds marked, a first-vs-last-six-months decline-rate comparison, and a sortable segment table.

### Underwriting notes (was the whole app)
- Same loop and DATA RULES, plus: a scope picker (whole book or one category), staged progress steps, a streaming reveal, the verifier's flags above the note, sources (fact-pack rows, tables, window, model, latency) under it, and a note library.
- **Fact pack:** the old pack compared the first and last month-end only, which (because of the data bug below) held one category each. It now has per-segment totals for the full window, first-6 vs last-6-month change, decline-reason counts and the CFPB backdrop for both periods.
- **Reserve:** notes and tiles use the average reserve on *booked* (approved and referred) merchants. The old average counted declines as 0%, which understated it. The semantic view keeps the original metric and says so in its comment.
- **Fixes:**
  - `AI_COMPLETE` returns its text JSON-encoded through Snowpark (`"..."` with escapes); it is decoded before use, in the verifier too.
  - The verifier now writes a reason first, takes the last JSON object it emits, and is told which words count as hedges (uncertainty words, not "sharply" or "elevated") and that 2026 dates are historical. Before that, it flagged correct notes for "future dates" and descriptive words.
  - `MERCHANT_RISK_REPORTS` also stores the flags, fact pack, model and latency.
- On the synthetic data, 6 of 7 notes verify. The one flag is a verifier mistake (it rejected a correct total of 38 declines), kept as an honest example of **Needs review**.

### Ask the agent (new in the app)
- The agent existed before but only in Snowsight. The app now calls it with `SNOWFLAKE.CORTEX.DATA_AGENT_RUN` and shows staged steps, the answer, the result table and the SQL Cortex Analyst wrote. Live mode also accepts typed questions.
- The agent spec gains an `execution_environment` warehouse and a "do not name real companies" instruction.

### Landing page (`docs/index.html`, replaces the root `index.html`)
- Its own identity: an oxblood hero with the threshold rail drawn from the pack's 720 applications, a problem-first headline, a needs/time/cost strip, six captioned screenshots with alt text, a "how Snowflake does each step" table with measured times, run options, a disclaimer and doc links. Works at phone width; no CDN scripts (fonts are bundled). Not done: a dark-mode variant.

### Hosted example (`docs/try/`, replaces the root `try/`)
- A dependency-free static copy of all five screens on the same data, with SVG charts and tooltips, a sortable and filterable queue, a detail drawer, staged AI with a streaming reveal and the "Sample AI response" label. The Live button explains how to run Live mode.

## Data, SQL and repo

- **Seeded generator:** `data/generate.py` (seed `20260630`) replaces `RANDOM()` in SQL and keeps the original drivers and formulas. It writes `data/*.csv`, `app/sample/*.csv` and the INSERT block in `sql/setup.sql`. Planted stories are in [`data/README.md`](data/README.md).
- **Data bug fixed:** category came from `row % 6` and month from `row % 24`, so each category landed in only 4 of 24 months. Months now come from `(row ÷ 6) % 24`. Two stories are planted (Electronics chargeback drift in 2026, a thin-history restaurant wave in Q2 2026).
- **SQL:** `app/setup.sql`, `app/setup_synthetic.sql` and `app/teardown.sql` become:
  - `sql/setup.sql`: the synthetic setup, plus a least-privilege `MERCHANT_RISK_ROLE` that owns everything, the `MERCHANT_RISK_SCORE_FACTORS` and `MERCHANT_RISK_BOOK` views, extra columns on `MERCHANT_RISK_REPORTS`, an `APP_STAGE` stage, and re-run-safe drops. Score arithmetic uses NUMBER types so Snowflake and Python round identically.
  - `sql/cfpb_live_backdrop.sql`: the original real-CFPB view as an optional add-on run after setup (the two old setup files differed only there).
  - `sql/cleanup.sql`: drops the objects as the pack role, then the role; safe to run twice.
- **Notebook:** prerequisites now point to `sql/setup.sql`; the code is unchanged and uses the same objects.
- **Removed:** the root `styles.css` and `assets/` (old screenshots). The root `index.html` and `try/index.html` are now redirect stubs to `docs/`, so existing links keep working.
- **Added:** `app/` modules `data.py`, `ai.py`, `brand.py`, `views/`, `static/fonts/`, `.streamlit/config.toml`, `requirements.txt` and `environment.yml` pinned to Streamlit 1.50.0; `scripts/capture_sample.py` (Live → Sample AI) and `scripts/build_example.py`; `package.json` with `npm run build:example`; `.gitignore`.
- **Verified live** on 2026-11-21 in a Snowflake demo account with key-pair auth:
  - setup ran in 17 s, twice in a row;
  - all 720 Live rows (score, decision, reason, reserve, factors) and the 24 backdrop months equal the Sample data;
  - every screen ran in Live mode in a browser at desktop and 390 px with no errors or sideways scroll;
  - notes took 9–19 s; agent answers 8–27 s, including a typed question answered correctly;
  - `CREATE STREAMLIT` from the stage on the warehouse runtime succeeded;
  - cleanup left nothing behind (checked with SHOW).
  - Not run: `sql/cfpb_live_backdrop.sql` (the CFPB listing was not mounted in the test account) and the notebook.

## What to do after merging

1. **Pull:** after you merge the PR, run `git pull` on `main` in your local clone to bring it up to date.
2. **Pages:** Settings → Pages → Build and deployment → *Deploy from a branch*, branch `main`, folder **`/docs`** (it was `/ (root)`). `docs/.nojekyll` is included. The root redirect stubs keep old links working either way.
3. After Pages redeploys, open `https://sfc-gh-jsoliz.github.io/sfguide-merchant-risk/` and `/try/`, and check that every CSS and JS file referenced from `/try/index.html` returns 200 (`app.css`, `app.js`, `data.js`, `../assets/tokens.css`).
4. Optional: Settings → *Template repository*, and topics (`snowflake`, `financial-services`, `payments`, `underwriting`, `cortex`).
5. Rebuild commands, if you change the data or the AI samples:

   ```bash
   python3 data/generate.py              # regenerate data and the setup.sql data block
   # run sql/setup.sql, then with Live env vars set (see README):
   python3 scripts/capture_sample.py     # recapture Sample AI responses from Live
   npm run build:example                 # or: python3 scripts/build_example.py
   ```

6. New catalog cards are ready in `docs/images/cards/merchant-risk-1.jpg` … `-6.jpg` (960×600, under 100 KB each, dashboard first) for the catalog PR.
7. For your next v2 upgrade, give your CoCo [`COCO-V2-INSTRUCTIONS.md`](COCO-V2-INSTRUCTIONS.md) together with this file as a worked example.
