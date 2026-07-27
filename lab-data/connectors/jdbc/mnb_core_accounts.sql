-- Meridian lab schema for JDBC connector lessons (PostgreSQL / MySQL compatible-ish)
CREATE TABLE IF NOT EXISTS mnb_app_accounts (
  account_id   VARCHAR(64) PRIMARY KEY,
  username     VARCHAR(128) NOT NULL,
  email        VARCHAR(256),
  employee_id  VARCHAR(32),
  status       VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
  entitlement  VARCHAR(64),
  updated_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS mnb_app_entitlements (
  entitlement_code VARCHAR(64) PRIMARY KEY,
  display_name     VARCHAR(128) NOT NULL,
  risk_tier        VARCHAR(16) NOT NULL
);
