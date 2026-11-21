-- ============================================================================
-- Merchant Risk & Underwriting - sql/cfpb_live_backdrop.sql  (optional)
-- ----------------------------------------------------------------------------
-- Swaps the synthetic CFPB backdrop for the REAL free CFPB Complaint Database
-- from Snowflake Marketplace (payment products only), keeping the synthetic
-- application book. Everything downstream (views, semantic view, agent, app)
-- is unchanged. The app then shows "Real CFPB backdrop" in its source line.
--
-- Prereqs: run sql/setup.sql first, then in Snowsight > Marketplace get the
-- free "CFPB Complaint Database" listing and mount it as CFPB_COMPLAINT.
-- Not run in the v2 live verification (the listing was not mounted in the
-- test account); the view body is unchanged from the original pack's setup.sql.
-- Undo: re-run sql/setup.sql.
-- ============================================================================
USE ROLE ACCOUNTADMIN;
GRANT IMPORTED PRIVILEGES ON DATABASE CFPB_COMPLAINT TO ROLE MERCHANT_RISK_ROLE;

USE ROLE MERCHANT_RISK_ROLE;
USE WAREHOUSE SNOWPACK_MERCHANT_RISK_WH;
USE SCHEMA SNOWPACK_MERCHANT_RISK.CORE;
DROP TABLE IF EXISTS MERCHANT_RISK_CFPB_BENCHMARK;
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

CREATE OR REPLACE VIEW MERCHANT_RISK_DATA_SOURCE_INFO AS
SELECT 'marketplace' AS mode,
       'Synthetic application/decision book cross-referenced against the REAL free CFPB Complaint Database (payment-product complaint intensity by month).' AS note;

SELECT COUNT(*) AS cfpb_months FROM MERCHANT_RISK_CFPB_BENCHMARK;
