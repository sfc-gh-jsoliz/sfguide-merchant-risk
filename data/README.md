# Synthetic data

Everything in this pack is synthetic. `data/generate.py` builds it with a fixed seed (`20260630`), so every run writes the same numbers, byte for byte:

```bash
python3 data/generate.py
```

| File | Rows | What it holds |
|---|---|---|
| `categories.csv` | 6 | Merchant category, MCC and base risk weight |
| `applications.csv` | 720 | One new-merchant application each: category, credit tier, requested monthly volume, years trading, prior-processor flag, chargeback history (bps), application month-end |
| `decisions.csv` | 720 | Risk score, approve / refer / decline, decline reason and reserve %, computed with the same rules as `sql/setup.sql` |
| `cfpb_monthly.csv` | 24 | Synthetic CFPB-style monthly payment-complaint count, % closed with monetary relief, % timely response |

The same rows are copied to `app/sample/` (read in Sample mode) and pasted into `sql/setup.sql` between the `GENERATED DATA` markers. In Live mode Snowflake recomputes the score, decision, reason and reserve in SQL from the applications; the build checked that all 720 Live rows equal the Sample rows.

## How the numbers are made

The original pack's drivers and formulas, with a seeded Python RNG in place of Snowflake `RANDOM()`:

- 720 applications, 6 categories × 24 months (July 2024 to June 2026), 5 per category per month.
- Credit tier uniform over A-Prime, B-NearPrime, C-Subprime, D-HighRisk; requested volume $5K–$500K a month; 0–25 years trading; prior-processor flag 0/1; chargebacks 0–400 bps.
- Score, thresholds, reasons and reserve as in the README's *How the score works*.
- CFPB backdrop: 9,000 + up to 2,500 + 60 × month index complaints; 22–30% monetary relief; 97–100% timely.

**Fix from the original:** the original assigned category by `row % 6` and month by `row % 24`. Those share a factor, so each category appeared in only 4 of the 24 months and a first-month vs last-month comparison covered one category each. Months now come from `(row ÷ 6) % 24`.

## Planted stories

On this synthetic data set:

1. **Electronics chargeback drift (Jan–Jun 2026).** Electronics & Appliances applications in 2026 draw chargebacks from 140–400 bps instead of 0–400. Average chargebacks rise from 193 to 261 bps and the decline rate from 75.6% (Jul 2024–Dec 2025, 90 applications) to 83.3% (30 applications). The Portfolio insight and the Segments dumbbell show it.
2. **Thin-history restaurant wave (Apr–Jun 2026).** Restaurants & Food Service applicants in the last quarter have 0–1 years trading. Their decline rate is 86.7% (15 applications) against 56.2% before (105), and 4 of the book's 13 "Thin operating history" declines fall in that quarter.

Stories that follow from the original formula:

3. **Category spread.** Electronics & Appliances declines 77.5% and Restaurants 60.0%; Food & Beverage Stores declines 4.2% and approves 36.7%, the highest of any category.
4. **Credit tier.** D-HighRisk declines 58.7% of 201 applications; A-Prime 14.1% of 170.
5. **Decline reasons.** High chargeback history accounts for 190 of 252 declines.
