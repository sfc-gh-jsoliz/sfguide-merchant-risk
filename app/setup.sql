-- ============================================================================
-- Isolated setup: dedicated database, schema, and warehouse for this Snow Pack.
CREATE DATABASE IF NOT EXISTS SNOWPACK_MERCHANT_RISK;
CREATE SCHEMA IF NOT EXISTS SNOWPACK_MERCHANT_RISK.CORE;
CREATE WAREHOUSE IF NOT EXISTS SNOWPACK_MERCHANT_RISK_WH WITH WAREHOUSE_SIZE='XSMALL' AUTO_SUSPEND=60 AUTO_RESUME=TRUE INITIALLY_SUSPENDED=TRUE;
USE WAREHOUSE SNOWPACK_MERCHANT_RISK_WH;
USE SCHEMA SNOWPACK_MERCHANT_RISK.CORE;
-- ============================================================================
-- Merchant Risk & Underwriting — setup.sql  (deploy mode: real CFPB complaint data)
-- ----------------------------------------------------------------------------
-- Scores new-merchant applications (category, chargeback history, tenure, credit
-- tier) into approve / refer / decline, and cross-references a REAL external
-- risk backdrop: CFPB consumer-complaint intensity for payment products, from
-- the free Snowflake Marketplace "CFPB Complaint Database"
-- (CFPB_COMPLAINT.DERIVED.CFPB_COMPLAINT_MAPPED).
--
-- A processor's own application/decision book has no public source, so
-- MERCHANT_RISK_APPLICATION / MERCHANT_RISK_DECISION are synthetic in both modes;
-- here the CFPB backdrop is REAL. To use your own book, replace the APPLICATION
-- and DECISION tables with your intake/decision data (same columns) via Cortex Code.
--
-- Prereq: mount the free "CFPB Complaint Database" listing from the Marketplace.
-- Run setup_synthetic.sql instead for a no-listing TRY.
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS SNOWPACK_MERCHANT_RISK.CORE
  COMMENT = 'Merchant Risk & Underwriting Snow Pack';
USE SCHEMA SNOWPACK_MERCHANT_RISK.CORE;

-- 0. Type-switch drops (CFPB backdrop is a VIEW here, a TABLE in setup_synthetic)
DROP VIEW IF EXISTS MERCHANT_RISK_SV;
DROP VIEW IF EXISTS MERCHANT_RISK_BENCHMARK;
DROP TABLE IF EXISTS MERCHANT_RISK_CFPB_BENCHMARK;
DROP VIEW IF EXISTS MERCHANT_RISK_CFPB_BENCHMARK;

-- 1. Merchant category dimension (MCC-aligned) with a base risk weight ---------
CREATE OR REPLACE TABLE MERCHANT_RISK_CATEGORY (
  category_code STRING, category_name STRING, mcc STRING, base_risk FLOAT
);
INSERT INTO MERCHANT_RISK_CATEGORY VALUES
  ('RESTAURANTS','Restaurants & Food Service','5812',55),
  ('APPAREL','Clothing & Accessories','5651',40),
  ('ELECTRONICS','Electronics & Appliances','5732',62),
  ('GROCERY','Food & Beverage Stores','5411',28),
  ('FURNITURE','Furniture & Home Furnishings','5712',45),
  ('HEALTH','Health & Personal Care','5912',35);

-- 24 application months ending 2026-06-30 -------------------------------------
CREATE OR REPLACE TEMP TABLE MERCHANT_RISK_months AS
SELECT LAST_DAY(DATEADD(month, SEQ4(), '2024-07-01')) AS month_end, SEQ4() AS m_idx
FROM TABLE(GENERATOR(ROWCOUNT => 24));

-- Deterministic application+decision generator (fixed RNG seeds for stable re-runs)
CREATE OR REPLACE TEMP TABLE MERCHANT_RISK_drivers AS
WITH _cat AS (
  SELECT c.*, (ROW_NUMBER() OVER (ORDER BY c.category_code)) - 1 AS cat_idx
  FROM MERCHANT_RISK_CATEGORY c
),
_app AS (
  SELECT
    'APP-' || LPAD(SEQ4()::string, 6, '0') AS application_id,
    MOD(SEQ4(), 6)  AS cat_idx,
    MOD(SEQ4(), 24) AS mon_idx,
    UNIFORM(1, 4, RANDOM(101))        AS tier_idx,
    UNIFORM(5000, 500000, RANDOM(102)) AS requested_monthly_volume,
    UNIFORM(0, 25, RANDOM(103))        AS years_in_business,
    UNIFORM(0, 1, RANDOM(104))         AS prior_processor_flag,
    UNIFORM(0, 400, RANDOM(105))       AS chargeback_history_bps
  FROM TABLE(GENERATOR(ROWCOUNT => 720))
)
SELECT
  a.application_id,
  c.category_name || ' Merchant #' || RIGHT(a.application_id, 4) AS merchant_name,
  c.category_code, c.category_name, c.mcc,
  CASE a.tier_idx WHEN 1 THEN 'A-Prime' WHEN 2 THEN 'B-NearPrime' WHEN 3 THEN 'C-Subprime' ELSE 'D-HighRisk' END AS credit_tier,
  a.requested_monthly_volume, a.years_in_business, a.prior_processor_flag, a.chargeback_history_bps,
  m.month_end,
  LEAST(100, GREATEST(0, ROUND(
    c.base_risk
    + a.chargeback_history_bps / 10.0
    + (a.tier_idx - 1) * 8
    - LEAST(a.years_in_business, 15) * 1.2
    - a.prior_processor_flag * 5
  , 1))) AS risk_score
FROM _app a
JOIN _cat c ON a.cat_idx = c.cat_idx
JOIN MERCHANT_RISK_months m ON a.mon_idx = m.m_idx;

-- 2. Application book (synthetic; swap for your intake data) -------------------
CREATE OR REPLACE TABLE MERCHANT_RISK_APPLICATION
  COMMENT = 'SYNTHETIC: new-merchant underwriting applications. Replace with your own application intake (same columns) to go live.'
AS
SELECT application_id, merchant_name, mcc, category_code, category_name, credit_tier,
       requested_monthly_volume, years_in_business, prior_processor_flag,
       chargeback_history_bps, month_end
FROM MERCHANT_RISK_drivers;

-- 3. Decision book (synthetic; risk score drives approve/refer/decline) --------
CREATE OR REPLACE TABLE MERCHANT_RISK_DECISION
  COMMENT = 'SYNTHETIC: underwriting decisions derived from risk score (category, chargeback history, tenure, credit tier).'
AS
SELECT application_id,
       CASE WHEN risk_score < 40 THEN 'approve'
            WHEN risk_score < 70 THEN 'refer'
            ELSE 'decline' END AS decision,
       risk_score,
       CASE WHEN risk_score >= 70 AND chargeback_history_bps >= 200 THEN 'High chargeback history'
            WHEN risk_score >= 70 AND years_in_business < 2        THEN 'Thin operating history'
            WHEN risk_score >= 70 AND category_name = 'Electronics & Appliances' THEN 'High-risk category'
            WHEN risk_score >= 70                                  THEN 'Composite risk over threshold'
            ELSE NULL END AS decline_reason,
       CASE WHEN risk_score < 40 THEN ROUND(risk_score / 20.0, 2)
            WHEN risk_score < 70 THEN ROUND(risk_score / 10.0, 2)
            ELSE 0 END AS reserve_pct
FROM MERCHANT_RISK_drivers;

-- 4. CFPB complaint backdrop — REAL free CFPB Complaint Database ---------------
--    Monthly complaint intensity for payment products (latest vintage per row).
CREATE OR REPLACE VIEW MERCHANT_RISK_CFPB_BENCHMARK
  COMMENT = 'REAL monthly CFPB complaint backdrop for payment products, from the free CFPB Complaint Database (CFPB_COMPLAINT.DERIVED.CFPB_COMPLAINT_MAPPED).'
AS
SELECT
  LAST_DAY(DATE_RECEIVED) AS cfpb_month,
  COUNT(*) AS complaint_count,
  ROUND(100.0 * SUM(IFF(COMPANY_RESPONSE_TO_CONSUMER ILIKE '%monetary relief%', 1, 0)) / NULLIF(COUNT(*), 0), 2) AS pct_monetary_relief,
  ROUND(100.0 * SUM(IFF(TIMELY_RESPONSE, 1, 0)) / NULLIF(COUNT(*), 0), 2) AS pct_timely_response
FROM CFPB_COMPLAINT.DERIVED.CFPB_COMPLAINT_MAPPED
WHERE PRODUCT IN (
  'Credit card',
  'Credit card or prepaid card',
  'Money transfer, virtual currency, or money service',
  'Prepaid card'
)
GROUP BY LAST_DAY(DATE_RECEIVED);

-- 5. Wide benchmark view: synthetic book pre-aggregated to
--    (category, credit_tier, decision, month) + CFPB backdrop attached by month.
--    CFPB columns use MAX so the per-month value is attached non-additively.
CREATE OR REPLACE VIEW MERCHANT_RISK_BENCHMARK
  COMMENT = 'Underwriting portfolio by category/credit tier/decision/month with REAL CFPB complaint backdrop (per-month, non-additive).'
AS
SELECT
  a.category_code, a.category_name, a.credit_tier, d.decision, a.month_end,
  COUNT(*)                                   AS application_count,
  SUM(a.requested_monthly_volume)            AS requested_volume_usd,
  SUM(d.risk_score)                          AS risk_score_sum,
  SUM(d.reserve_pct)                         AS reserve_pct_sum,
  SUM(IFF(d.decision = 'approve', 1, 0))     AS approved_count,
  SUM(IFF(d.decision = 'decline', 1, 0))     AS declined_count,
  SUM(IFF(d.decision = 'refer', 1, 0))       AS referred_count,
  MAX(cf.complaint_count)                    AS cfpb_complaint_count,
  MAX(cf.pct_monetary_relief)                AS cfpb_pct_monetary_relief,
  MAX(cf.pct_timely_response)                AS cfpb_pct_timely_response
FROM MERCHANT_RISK_APPLICATION a
JOIN MERCHANT_RISK_DECISION d USING (application_id)
LEFT JOIN MERCHANT_RISK_CFPB_BENCHMARK cf ON cf.cfpb_month = a.month_end
GROUP BY a.category_code, a.category_name, a.credit_tier, d.decision, a.month_end;

-- 6. Data-source marker -------------------------------------------------------
CREATE OR REPLACE VIEW MERCHANT_RISK_DATA_SOURCE_INFO AS
SELECT 'marketplace' AS mode,
       'Synthetic application/decision book cross-referenced against the REAL free CFPB Complaint Database (payment-product complaint intensity by month).' AS note;

-- 7. Semantic view (single wide view; composite PK = true grain) ---------------
CREATE OR REPLACE SEMANTIC VIEW MERCHANT_RISK_SV
  TABLES ( mr AS SNOWPACK_MERCHANT_RISK.CORE.MERCHANT_RISK_BENCHMARK
           PRIMARY KEY (category_code, credit_tier, decision, month_end)
           WITH SYNONYMS = ('merchant risk','underwriting','application decisions')
           COMMENT = 'Underwriting applications/decisions by category, credit tier, decision and month with CFPB backdrop' )
  FACTS (
    mr.application_count AS application_count,
    mr.requested_volume_usd AS requested_volume_usd,
    mr.risk_score_sum AS risk_score_sum,
    mr.reserve_pct_sum AS reserve_pct_sum,
    mr.approved_count AS approved_count,
    mr.declined_count AS declined_count,
    mr.referred_count AS referred_count,
    mr.cfpb_complaint_count AS cfpb_complaint_count,
    mr.cfpb_pct_monetary_relief AS cfpb_pct_monetary_relief,
    mr.cfpb_pct_timely_response AS cfpb_pct_timely_response
  )
  DIMENSIONS (
    mr.category_name AS CATEGORY_NAME WITH SYNONYMS = ('merchant category','vertical','segment') COMMENT = 'Merchant category (MCC-aligned)',
    mr.category_code AS CATEGORY_CODE,
    mr.credit_tier AS CREDIT_TIER WITH SYNONYMS = ('tier','risk tier','credit band') COMMENT = 'Applicant credit tier',
    mr.decision AS DECISION WITH SYNONYMS = ('outcome','underwriting decision') COMMENT = 'approve / refer / decline',
    mr.month_end AS MONTH_END WITH SYNONYMS = ('month','period','as of'),
    mr.report_year AS YEAR(month_end) WITH SYNONYMS = ('year')
  )
  METRICS (
    mr.applications AS SUM(mr.application_count) COMMENT = 'Total applications',
    mr.total_requested_volume AS SUM(mr.requested_volume_usd) COMMENT = 'Total requested monthly volume (USD)',
    mr.approval_rate AS SUM(mr.approved_count) / NULLIF(SUM(mr.application_count), 0) COMMENT = 'Approved / total applications',
    mr.decline_rate AS SUM(mr.declined_count) / NULLIF(SUM(mr.application_count), 0) COMMENT = 'Declined / total applications',
    mr.avg_risk_score AS SUM(mr.risk_score_sum) / NULLIF(SUM(mr.application_count), 0) COMMENT = 'Average risk score (0-100)',
    mr.avg_reserve_pct AS SUM(mr.reserve_pct_sum) / NULLIF(SUM(mr.application_count), 0) COMMENT = 'Average reserve percentage',
    mr.avg_cfpb_complaints AS AVG(mr.cfpb_complaint_count) COMMENT = 'Average monthly CFPB complaints (payment products, non-additive)',
    mr.avg_cfpb_pct_monetary_relief AS AVG(mr.cfpb_pct_monetary_relief) COMMENT = 'Average CFPB pct closed with monetary relief (non-additive)'
  )
  COMMENT = 'Merchant-risk underwriting semantic view (synthetic book vs REAL CFPB complaint backdrop).';

-- 8. Output table + agent -----------------------------------------------------
CREATE TABLE IF NOT EXISTS MERCHANT_RISK_REPORTS (
  run_id STRING DEFAULT UUID_STRING(), subject STRING, draft_md STRING, report_md STRING,
  status STRING, edits_applied INT, residual_hedges INT, created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

CREATE OR REPLACE AGENT MERCHANT_RISK_AGENT
  COMMENT = 'Merchant Risk & Underwriting agent (Cortex Analyst over MERCHANT_RISK_SV)'
  PROFILE = '{"display_name": "Merchant Risk Agent", "color": "blue"}'
  FROM SPECIFICATION
  $$
  models:
    orchestration: auto
  instructions:
    response: 'You are a merchant-underwriting analyst. Use ONLY figures from the Analyst tool. risk_score is 0-100 (higher = riskier). Express USD in $B/$M and rates as percentages. CFPB complaint figures are an external industry backdrop (payment products), not this processor''s own complaints. Never invent numbers. Be concise and cite the month.'
    orchestration: 'For any application, approval, decline, risk-score, reserve, or CFPB complaint question use the MerchantRisk Analyst tool.'
    sample_questions:
      - question: 'Which merchant categories have the highest decline rate?'
      - question: 'How does the average risk score for C-Subprime compare to A-Prime?'
  tools:
    - tool_spec:
        type: cortex_analyst_text_to_sql
        name: MerchantRisk
        description: 'Underwriting applications/decisions by category, credit tier, decision and month, with a CFPB complaint-intensity backdrop.'
  tool_resources:
    MerchantRisk:
      semantic_view: SNOWPACK_MERCHANT_RISK.CORE.MERCHANT_RISK_SV
  $$;
