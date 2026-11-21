"""Seeded synthetic data for Merchant Risk & Underwriting.

Writes data/*.csv, copies them to app/sample/ (Sample mode) and pastes the INSERT
block into sql/setup.sql between the GENERATED DATA markers (Live mode), so both
modes show identical numbers. Same seed, same output, byte for byte:

    python3 data/generate.py

The drivers and formulas are the original pack's (setup_synthetic.sql); only the
noise source changed from Snowflake RANDOM() to a seeded Python RNG. Planted
stories are documented in data/README.md.
"""
import csv
import random
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

SEED = 20260630
ROOT = Path(__file__).resolve().parent.parent
N_APPS = 720
N_MONTHS = 24

# (category_code, category_name, mcc, base_risk): unchanged from the original pack
CATEGORIES = [
    ("RESTAURANTS", "Restaurants & Food Service", "5812", 55),
    ("APPAREL", "Clothing & Accessories", "5651", 40),
    ("ELECTRONICS", "Electronics & Appliances", "5732", 62),
    ("GROCERY", "Food & Beverage Stores", "5411", 28),
    ("FURNITURE", "Furniture & Home Furnishings", "5712", 45),
    ("HEALTH", "Health & Personal Care", "5912", 35),
]
CATEGORIES.sort(key=lambda c: c[0])  # the original joined on ROW_NUMBER() OVER (ORDER BY category_code)
TIERS = {1: "A-Prime", 2: "B-NearPrime", 3: "C-Subprime", 4: "D-HighRisk"}


def month_end(i):
    first = date(2024 + (6 + i) // 12, (6 + i) % 12 + 1, 1)
    nxt = date(first.year + first.month // 12, first.month % 12 + 1, 1)
    return (nxt - timedelta(days=1)).isoformat()


MONTHS = [month_end(i) for i in range(N_MONTHS)]


def q(x, places):
    return Decimal(x).quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_UP)


def risk_score(base, cb_bps, tier, years, prior):
    s = (Decimal(base) + Decimal(cb_bps) / 10 + (tier - 1) * 8
         - min(years, 15) * Decimal("1.2") - prior * 5)
    return q(min(Decimal(100), max(Decimal(0), s)), 1)


def decide(score, cb_bps, years, category_name):
    if score < 40:
        decision = "approve"
    elif score < 70:
        decision = "refer"
    else:
        decision = "decline"
    reason = None
    if score >= 70:
        if cb_bps >= 200:
            reason = "High chargeback history"
        elif years < 2:
            reason = "Thin operating history"
        elif category_name == "Electronics & Appliances":
            reason = "High-risk category"
        else:
            reason = "Composite risk over threshold"
    if score < 40:
        reserve = q(score / 20, 2)
    elif score < 70:
        reserve = q(score / 10, 2)
    else:
        reserve = Decimal("0.00")
    return decision, reason, reserve


def build():
    rng = random.Random(SEED)
    apps, decisions = [], []
    for i in range(N_APPS):
        code, name, mcc, base = CATEGORIES[i % 6]
        m = (i // 6) % N_MONTHS  # fix: the original used i % 24, so each category only landed in 4 of 24 months
        tier = rng.randint(1, 4)
        volume = rng.randint(5000, 500000)
        years = rng.randint(0, 25)
        prior = rng.randint(0, 1)
        cb = rng.randint(0, 400)
        # Planted story 1: Electronics chargeback drift, Jan-Jun 2026
        if code == "ELECTRONICS" and m >= 18:
            cb = rng.randint(140, 400)
        # Planted story 2: thin-history Restaurants wave, Apr-Jun 2026
        if code == "RESTAURANTS" and m >= 21:
            years = rng.randint(0, 1)
        app_id = f"APP-{i:06d}"
        apps.append({
            "application_id": app_id, "merchant_name": f"{name} Merchant #{app_id[-4:]}", "mcc": mcc,
            "category_code": code, "category_name": name, "credit_tier": TIERS[tier],
            "requested_monthly_volume": volume, "years_in_business": years, "prior_processor_flag": prior,
            "chargeback_history_bps": cb, "month_end": MONTHS[m],
        })
        score = risk_score(base, cb, tier, years, prior)
        decision, reason, reserve = decide(score, cb, years, name)
        decisions.append({"application_id": app_id, "decision": decision, "risk_score": str(score),
                          "decline_reason": reason or "", "reserve_pct": str(reserve)})
    cfpb = []
    for i in range(N_MONTHS):  # original: 9000 + U(0,2500) + i*60, 22 + U(0,8), 97 + U(0,3)
        cfpb.append({"cfpb_month": MONTHS[i], "complaint_count": 9000 + rng.randint(0, 2500) + i * 60,
                     "pct_monetary_relief": str(q(22 + rng.randint(0, 8), 2)),
                     "pct_timely_response": str(q(97 + rng.randint(0, 3), 2))})
    cats = [{"category_code": c, "category_name": n, "mcc": m, "base_risk": b} for c, n, m, b in CATEGORIES]
    return cats, apps, decisions, cfpb


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def lit(v):
    if v is None or v == "":
        return "NULL"
    if isinstance(v, int):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def inserts(table, rows, cols):
    out = [f"INSERT INTO {table} ({', '.join(cols)}) VALUES"]
    out.append(",\n".join("  (" + ", ".join(lit(r[c]) for c in cols) + ")" for r in rows) + ";")
    return "\n".join(out)


def main():
    cats, apps, decisions, cfpb = build()
    files = {"categories.csv": cats, "applications.csv": apps, "decisions.csv": decisions, "cfpb_monthly.csv": cfpb}
    for name, rows in files.items():
        write_csv(ROOT / "data" / name, rows)
        write_csv(ROOT / "app" / "sample" / name, rows)
    block = "\n\n".join([
        f"-- Generated by data/generate.py (seed {SEED}). Do not edit by hand.",
        inserts("MERCHANT_RISK_CATEGORY", cats, ["category_code", "category_name", "mcc", "base_risk"]),
        inserts("MERCHANT_RISK_APPLICATION", apps, list(apps[0])),
        inserts("MERCHANT_RISK_CFPB_BENCHMARK", cfpb, list(cfpb[0])),
    ])
    sql = ROOT / "sql" / "setup.sql"
    text = sql.read_text()
    a, b = "-- BEGIN GENERATED DATA\n", "\n-- END GENERATED DATA"
    s, e = text.index(a) + len(a), text.index(b)
    sql.write_text(text[:s] + block + text[e:])
    n = {d: sum(1 for r in decisions if r["decision"] == d) for d in ("approve", "refer", "decline")}
    print(f"{len(apps)} applications ({n}), {len(cfpb)} CFPB months; wrote data/, app/sample/, sql/setup.sql")


if __name__ == "__main__":
    main()
