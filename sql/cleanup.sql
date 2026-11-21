-- ============================================================================
-- Merchant Risk & Underwriting - sql/cleanup.sql
-- Removes everything sql/setup.sql created: the database (tables, views,
-- semantic view, agent, notes, stage, Streamlit app), the warehouse and the
-- role. Objects are owned by MERCHANT_RISK_ROLE, so they are dropped as that
-- role; ACCOUNTADMIN then drops the role. Safe to run twice. The free CFPB
-- Complaint Database listing, if you mounted it, is not touched.
-- ============================================================================
USE ROLE ACCOUNTADMIN;
CREATE ROLE IF NOT EXISTS MERCHANT_RISK_ROLE;  -- no-op if it exists; lets a re-run continue
SET my_user = CURRENT_USER();
GRANT ROLE MERCHANT_RISK_ROLE TO USER IDENTIFIER($my_user);
USE ROLE MERCHANT_RISK_ROLE;
DROP DATABASE IF EXISTS SNOWPACK_MERCHANT_RISK;
DROP WAREHOUSE IF EXISTS SNOWPACK_MERCHANT_RISK_WH;
USE ROLE ACCOUNTADMIN;
DROP ROLE IF EXISTS MERCHANT_RISK_ROLE;
SHOW DATABASES LIKE 'SNOWPACK_MERCHANT_RISK';
