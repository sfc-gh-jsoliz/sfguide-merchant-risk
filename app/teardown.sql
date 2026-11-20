-- ============================================================================
-- Merchant Risk & Underwriting — teardown.sql
-- ----------------------------------------------------------------------------
-- Removes everything this Snow Pack created: the dedicated database (all tables,
-- views, semantic view, agent, and the Streamlit app) and the dedicated warehouse.
-- Safe to run whether you deployed the synthetic (setup_synthetic.sql) or the
-- real-CFPB (setup.sql) mode. The free external CFPB Complaint Database listing,
-- if mounted, is not affected.
-- ============================================================================

DROP DATABASE IF EXISTS SNOWPACK_MERCHANT_RISK;
DROP WAREHOUSE IF EXISTS SNOWPACK_MERCHANT_RISK_WH;
