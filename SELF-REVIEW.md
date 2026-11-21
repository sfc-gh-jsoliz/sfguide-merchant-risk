# Self-review (v2 rebuild, 2026-11-21)

Each item in the Snow Packs v2 self-check and every CONTRIBUTING **Must** (plus the Shoulds), marked **pass**, **fail** or **skipped**, checked on this branch.

## Before you call it done

| Check | Result |
|---|---|
| App runs from a fresh clone in Sample mode | **pass**: cloned `v2-rebuild` from GitHub, all five screens render with no exceptions; regenerating data leaves the tree unchanged |
| Setup → Live → cleanup in a clean role | **pass**: `sql/setup.sql` as `MERCHANT_RISK_ROLE` (17 s, run twice), every screen and AI feature in Live, `sql/cleanup.sql` (run twice), SHOW confirms database, warehouse and role are gone |
| Grep files and git history for secrets, account identifiers, user names | **pass**: every blob in the pushed history scanned for account locators, key material, local paths, tokens and internal hosts; none found. Commit authorship shows the two authors' work emails, as usual for git |
| Pages URL and `/try/` signed out, phone width | **pass**: fork preview from `v2-rebuild` `/docs`; every JS/CSS/font/image returns 200; 390 px and desktop with no sideways scroll or console errors |
| Dark mode | **skipped**: the design is light-only (DESIGN.md); no dark variant was built |
| Story beats visible in screenshots | **pass**: Electronics drift (Portfolio insight, Segments dumbbell), category and tier spread (Segments heatmap), decline reasons (Portfolio), verified note and agent answer |

## v2 requirements

| Check | Result |
|---|---|
| `docs/DESIGN.md` with brand, palette, type, layout, charts, motion, distinctness vs 5+ packs | **pass** (10 packs compared) |
| No coined product name; plain pack title | **pass**: "Merchant Risk & Underwriting" |
| Branded shell: navigation, logo, role chip, environment badge | **pass** |
| KPI tiles with trends, charts with tooltips and legends, sortable/filterable tables with status pills, detail panel, empty/loading/error states | **pass** (skeleton on Live load, empty filter state, Live errors shown, never sample data) |
| Motion: transitions, skeletons, hover, count-up | **pass**; reduced-motion respected |
| Contrast WCAG AA | **pass**: text pairs measured 5.0:1 to 15.3:1 |
| AI: 4–8 s staged steps, streaming reveal, sources, "Sample AI response" label | **pass** |
| Seeded deterministic generator, planted stories in `data/README.md` | **pass**: two runs byte-identical; Live rows equal Sample rows |
| Only Live-verified capabilities claimed; preview labels | **pass**: AI_COMPLETE, Cortex Agents, Cortex Analyst/semantic view, Streamlit in Snowflake all ran; the CFPB Marketplace add-on is marked not run. No preview features used |
| Key-pair auth only | **pass** |
| `docs/.nojekyll`; `/try/` assets 200 | **pass** |
| Landing page has its own identity, no CDN scripts | **pass** |
| V2-CHANGES.md and COCO-V2-INSTRUCTIONS.md | **pass** |

## CONTRIBUTING Musts

| Must | Result |
|---|---|
| Business problem, one industry (Payments) and function (Underwriting) | **pass** |
| Public `sfguide-<topic>` repo, Apache 2.0 LICENSE | **pass** (unchanged) |
| GitHub Pages enabled | **pass on the fork preview**; the owner switches his repo to `/docs` after merge (V2-CHANGES step 2) |
| Landing: problem first, screenshots of the running app, captions naming the capability, alt text | **pass** |
| Landing: Snowflake capability per step, only tested claims | **pass** |
| Landing: visible disclaimer; repo and docs links | **pass** (all doc links return 200) |
| No Snowflake logo files; no internal sales wording | **pass** |
| End-user app with workflow, drill-down and decision | **pass** |
| No-account mode; simulated output labeled | **pass** |
| Live mode on the same app | **pass** |
| Synthetic data only; self-contained setup (own database, XSMALL warehouse, 60 s suspend) | **pass** |
| Cleanup removes everything | **pass** |
| No credentials, identifiers or user names in code, screenshots, output or history | **pass**: screenshots are Sample mode; README uses `<YOUR_USER>` |
| No customer data, deals or internal programs; GA features | **pass** |
| README: prerequisites, run steps, objects table, cost and time, limitations, Customize with Cortex Code, owner and review date, licence and disclaimer | **pass** |
| Claims as possibilities; synthetic results qualified | **pass** |

## CONTRIBUTING Shoulds

| Should | Result |
|---|---|
| Sample/Live switch, default Live when configured, setup steps when not | **pass** |
| Simulated AI with staged truthful steps; Live shows measured latency | **pass** |
| Capability badges in the UI | **pass** |
| Phone width usable | **pass** |
| Least-privilege role | **pass** |
| Prerequisites, time and cost near the top of the landing page | **pass** |
| Landing page dark mode | **skipped** (light-only design) |
| Template repository, topics | **skipped**: settings on the owner's repo, listed in V2-CHANGES |
| Edition notes | **pass** (Enterprise recommended) |

## Not verified in this build

- `sql/cfpb_live_backdrop.sql`: the free CFPB listing was not mounted in the test account. The view body is unchanged from the original pack.
- `notebook/lab-merchant-risk.ipynb`: only its prerequisite text changed; it was not re-run.
- Cost: warehouse metering had not posted before cleanup; the README gives an estimate from measured time.
