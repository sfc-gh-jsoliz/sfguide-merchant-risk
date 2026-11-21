# Merchant Risk & Underwriting: design

The app and the landing page share one look, set out here. Tokens in `app/brand.py`, `docs/assets/tokens.css` and `app/.streamlit/config.toml` come from this file.

## Audience and voice

Underwriting analysts and risk-operations leads at a payments processor or merchant acquirer. They review new-merchant applications every day, decide approve / refer / decline, set a reserve, and have to justify each decision to credit committee and audit.

- **Voice:** a careful credit officer. Short declarative sentences, numbers first, no hype. "Refer: chargebacks at 260 bps, 1 year trading" rather than "This merchant looks risky!"
- **Words:** approve, refer, decline, reserve, score, threshold, book. Never "AI magic", never exclamation marks.
- **Name:** the app is titled with the pack's plain name, **Merchant Risk & Underwriting**. No product name.

## Logo mark

A risk gauge: a half-dial split into three arcs at the pack's thresholds (0–40 approve, 40–70 refer, 70–100 decline) with a needle. It reads as "a score against thresholds", which is what the app does. Inline SVG in `app/brand.py`, `docs/assets/logo.svg`.

```svg
<svg viewBox="0 0 32 32" width="30" height="30"><rect width="32" height="32" rx="7" fill="#5A1A28"/>
<path d="M6 21 A10 10 0 0 1 11.1 12.3" stroke="#7FD1A8" stroke-width="3" fill="none"/>
<path d="M12.9 11.4 A10 10 0 0 1 21.6 12.8" stroke="#F0C36A" stroke-width="3" fill="none"/>
<path d="M23.2 14.3 A10 10 0 0 1 26 21" stroke="#F29A8E" stroke-width="3" fill="none"/>
<path d="M16 21 L21 14.5" stroke="#FFF7F2" stroke-width="2" stroke-linecap="round"/><circle cx="16" cy="21" r="2.2" fill="#FFF7F2"/></svg>
```

## Palette

Light app on a warm stone canvas, with an oxblood brand colour and a steel-blue secondary. The three decision colours are reserved for decisions and nothing else, so a glance at any screen reads as a decision mix.

| Token | Hex | Use |
|---|---|---|
| `oxblood900` | `#3D1019` | Sidebar background, landing hero band |
| `oxblood700` | `#5A1A28` | Logo tile, primary buttons |
| `oxblood500` | `#7D2A3C` | Active nav marker, links, focus ring |
| `oxbloodSoft` | `#F4E6E8` | Selected rows, active chips |
| `stone` | `#F3F1EE` | App canvas |
| `surface` | `#FFFFFF` | Cards, tables |
| `surface2` | `#ECE8E3` | Table headers, inactive pills |
| `line` | `#DCD6CF` | Borders, dividers |
| `ink` | `#1E1A1B` | Body text (15.9:1 on stone) |
| `ink2` | `#4A4245` | Secondary text (8.6:1 on stone) |
| `muted` | `#655C5F` | Captions (5.9:1 on stone, 6.6:1 on white) |
| `steel` | `#36587A` | Secondary series, CFPB backdrop line |
| `approve` / `approveSoft` | `#1D6B47` / `#DDF0E5` | Approve (5.6:1 on its soft tint) |
| `refer` / `referSoft` | `#8A5A00` / `#FBEBCB` | Refer (5.1:1 on its soft tint) |
| `decline` / `declineSoft` | `#B02A1E` / `#F9E0DC` | Decline (5.4:1 on its soft tint) |

All text pairs meet WCAG AA (4.5:1); ratios were checked with the WCAG formula. The amber is darkened to `#8A5A00` because the brighter `#C98A12` fails on its tint.

## Typography

- **Instrument Sans** (OFL) for everything: headings 600, body 400, labels 500. It is a narrow, slightly technical grotesk that suits dense tables.
- **Red Hat Mono** (OFL) for scores, rates, amounts and IDs, with `tabular-nums`.
- Both ship as woff2 in `app/static/fonts/` and `docs/fonts/` with their OFL licences. Nothing loads from a CDN. If the fonts are missing (for example a paste-in Streamlit in Snowflake deploy), the stack falls back to the system UI font.

## Layout model and density

- **App:** a dark oxblood **left sidebar** holds the mark, the title, the Sample/Live switch, the environment badge, the role chip and the five screens. The main area is a 1240 px column on stone. On phones Streamlit collapses the sidebar behind its menu button, and the environment badge repeats at the top of each screen so the mode is always visible.
- **Screens:** Portfolio, Applications, Segments, Underwriting notes, Ask the agent.
- **Density:** medium-high. Tables use 0.84 rem rows; KPI tiles are compact (four or five across, two across on phones).
- **The threshold rail:** the signature element. A horizontal 0–100 bar split at 40 and 70 into approve / refer / decline bands, with each application as a tick. It appears in the Portfolio header, behind every score in the detail drawer and in the landing hero.

## Charts

- Altair in the app, hand-written SVG in the hosted example; both have tooltips and legends.
- Decision mix uses only the three decision colours, stacked approve → refer → decline from the baseline.
- Single-series charts use `oxblood500`; the CFPB backdrop always uses `steel` with a dashed stroke, so an external, non-additive series never looks like the processor's own numbers.
- Heatmaps run from `surface` to `decline` for decline rate and from `surface` to `oxblood500` for average score.
- Gridlines `#E7E1DA`, no chart borders, axis labels in `muted`.

## Motion

- Cards and tiles fade and rise 4 px on load (160 ms, staggered 30 ms).
- KPI figures count up once (CSS `@property`, 650 ms ease-out).
- Skeleton shimmer while Live data loads.
- AI runs show staged steps ticking in one by one, then the text reveals word by word.
- Threshold-rail ticks slide in from the left on first paint.
- `prefers-reduced-motion` turns all of it off.

## What makes it distinct

Live catalog packs and the other Payments v2 rebuilds checked on 2026-11-21 (landing pages and Try apps):

| Pack | Its look | What this pack avoids |
|---|---|---|
| Auto Finance Portfolio Analytics | Night navy, lime accent, mono type, dark sidebar with a mint hero card | No navy, no lime; sidebar is oxblood and there is no hero card in the app |
| Workforce Intelligence | Cream paper, plum, serif headings | No serif, no plum; stone canvas is grey-warm, not cream |
| Payment Fraud Workbench | Near-black UI with lime and pink signals | Light app, no neon |
| Collections Copilot | Lavender canvas, dusk violet, Bricolage Grotesque | No violet family, different typeface |
| Regulatory Change Tracker | Paper and red, IBM Plex Mono, Source Serif | No Plex or serif; red appears only as the decline signal |
| Loan File Review | Cobalt rail sidebar, Bricolage, Geist Mono | Oxblood not cobalt; Instrument Sans and Red Hat Mono |
| Cross-Border & FX (v2 branch) | Pine and saffron top bar, Space Grotesk, corridor-arc hero | Sidebar instead of top bar, no green brand colour, gauge/rail hero |
| Chargeback & Dispute Intelligence (v2 branch) | Teal masthead, mint, Sora | No teal or mint, no masthead |
| Verified Bank Research (v2 branch) | Black and gold, Newsreader serif | No gold, no serif |
| Macro Stress Testing (v2 branch) | Charcoal, cream and burnt orange, "stress fan" hero | No orange; stone not cream |

The landing hero is also new to the catalog: an oxblood band with the threshold rail drawn from the pack's own 720 applications (one tick per application, coloured by decision), not a screenshot on a gradient, a split hero or a typographic fan.
